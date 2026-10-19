import json
from collections.abc import Callable
from typing import cast

import httpx
import pytest

from app.mistral_chat import Chat, MistralCompletionsClient, Tool


def make_client(
    messages: list[dict[str, object]],
    requests: list[object] | None = None,
) -> MistralCompletionsClient:
    responses = [{"choices": [{"message": m}]} for m in messages]
    call_count = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        if requests is not None:
            requests.append(cast(object, json.loads(_req.content)))
        content = json.dumps(responses[call_count])
        call_count += 1
        return httpx.Response(200, content=content.encode())

    transport = httpx.MockTransport(handler)
    client = MistralCompletionsClient("dummy")
    client._client = httpx.AsyncClient(transport=transport)  # pyright: ignore[reportPrivateUsage]
    return client


# Starting a chat preserves the user prompt and assistant response.
@pytest.mark.anyio
async def test_start_chat() -> None:
    message: dict[str, object] = {"role": "assistant", "content": "foobar"}
    client = make_client([message])

    async with client:
        chat: Chat = await client.start_chat("abc")
    assert chat.messages == [
        {"role": "user", "content": "abc"},
        message,
    ]


# Follow-up turns retain the complete conversation history.
@pytest.mark.anyio
async def test_multi_turn_chat() -> None:
    client = make_client(
        [
            {"role": "assistant", "content": "first"},
            {"role": "assistant", "content": "second"},
        ]
    )

    async with client:
        chat1 = await client.start_chat("hello")
        chat2 = await chat1.chat("follow-up")
    assert chat2.messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "first"},
        {"role": "user", "content": "follow-up"},
        {"role": "assistant", "content": "second"},
    ]


# Mistral HTTP failures propagate to the caller.
@pytest.mark.anyio
async def test_http_error() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b'{"error": "boom"}')

    transport = httpx.MockTransport(handler)
    client = MistralCompletionsClient("dummy")
    client._client = httpx.AsyncClient(transport=transport)  # pyright: ignore[reportPrivateUsage]

    async with client:
        with pytest.raises(httpx.HTTPStatusError):
            _ = await client.start_chat("abc")


def add(a: int, b: int) -> int:
    return a + b


async def async_add(a: int, b: int) -> int:
    return a + b


def tool_call_message(name: str = "add") -> dict[str, object]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {"name": name, "arguments": '{"a": 2, "b": 3}'},
            }
        ],
    }


# Sync and async tool results reach the model before its final answer.
@pytest.mark.anyio
@pytest.mark.parametrize("fn", [add, async_add], ids=["sync", "async"])
async def test_tool_result_is_sent_back_to_model(fn: Callable[..., object]) -> None:
    requests: list[object] = []
    tool = Tool("add", fn, {"type": "function", "function": {"name": "add"}})
    call = tool_call_message()
    answer: dict[str, object] = {"role": "assistant", "content": "The sum is 5."}
    client = make_client([call, answer], requests)

    async with client:
        chat = await client.start_chat("Add 2 and 3", [tool])

    tool_result = {
        "role": "tool",
        "name": "add",
        "tool_call_id": "call-1",
        "content": "5",
    }
    history = [{"role": "user", "content": "Add 2 and 3"}, call, tool_result]
    assert requests[1] == {
        "model": "mistral-small-latest",
        "messages": history,
        "tools": [tool.meta],
        "tool_choice": "auto",
    }
    assert chat.messages == [*history, answer]


# Unregistered tool calls are rejected without executing a function.
@pytest.mark.anyio
@pytest.mark.parametrize("registered", [False, True], ids=["no-tools", "unknown-tool"])
async def test_unregistered_tool_is_rejected(registered: bool) -> None:
    client = make_client([tool_call_message("unknown")])
    calls: list[bool] = []

    def should_not_run(**_args: object) -> None:
        calls.append(True)

    tools = [Tool("add", should_not_run, {})] if registered else None
    async with client:
        with pytest.raises(ValueError, match="no tools|not allowed"):
            _ = await client.start_chat("hello", tools)
    assert calls == []


# Repeated tool calls stop at the configured round limit.
@pytest.mark.anyio
async def test_repeated_tool_calls_stop_at_round_limit() -> None:
    requests: list[object] = []
    client = make_client([tool_call_message()] * 6, requests)

    async with client:
        with pytest.raises(RuntimeError, match="Maximum tool-calling rounds exceeded"):
            _ = await client.start_chat("hello", [Tool("add", add, {})])

    assert len(requests) == 6
