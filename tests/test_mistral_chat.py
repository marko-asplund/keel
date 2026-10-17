import json

import httpx
import pytest

from app.mistral_chat import Chat, MistralCompletionsClient


def make_client(messages: list[dict[str, str]]) -> MistralCompletionsClient:
    responses = [{"choices": [{"message": m}]} for m in messages]
    call_count = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        content = json.dumps(responses[call_count])
        call_count += 1
        return httpx.Response(200, content=content.encode())

    transport = httpx.MockTransport(handler)
    client = MistralCompletionsClient("dummy")
    client._client = httpx.AsyncClient(transport=transport)  # pyright: ignore[reportPrivateUsage]
    return client


@pytest.mark.asyncio
async def test_start_chat() -> None:
    message: dict[str, str] = {"role": "assistant", "content": "foobar"}
    client = make_client([message])

    chat: Chat = await client.start_chat("abc")
    assert chat.messages == [
        {"role": "user", "content": "abc"},
        message,
    ]


@pytest.mark.asyncio
async def test_multi_turn_chat() -> None:
    client = make_client(
        [
            {"role": "assistant", "content": "first"},
            {"role": "assistant", "content": "second"},
        ]
    )

    chat1 = await client.start_chat("hello")
    chat2 = await chat1.chat("follow-up")
    assert chat2.messages == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "first"},
        {"role": "user", "content": "follow-up"},
        {"role": "assistant", "content": "second"},
    ]


@pytest.mark.asyncio
async def test_http_error() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b'{"error": "boom"}')

    transport = httpx.MockTransport(handler)
    client = MistralCompletionsClient("dummy")
    client._client = httpx.AsyncClient(transport=transport)  # pyright: ignore[reportPrivateUsage]

    with pytest.raises(httpx.HTTPStatusError):
        _ = await client.start_chat("abc")
