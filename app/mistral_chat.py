from __future__ import annotations

import json
from collections.abc import Callable
from typing import Self, cast

import httpx


class MistralCompletionsClient:
    _mistral_api_base_url: str = "https://api.mistral.ai"
    _default_model_name: str = "mistral-small-latest"

    def __init__(self, api_key: str):
        self._api_key: str = api_key
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=20.0)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    async def start_chat(self, prompt: str, tools: list[Tool] | None = None) -> Chat:
        messages: list[dict[str, object]] = [{"role": "user", "content": prompt}]
        return await self.chat(messages, tools)

    async def _chat_one_turn(
        self, messages: list[dict[str, object]], tools: list[Tool] | None
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {
            "model": self._default_model_name,
            "messages": messages,
        }
        if tools is not None:
            payload["tools"] = [t.meta for t in tools]
            payload["tool_choice"] = "auto"
        url = f"{self._mistral_api_base_url}/v1/chat/completions"
        r = await self._client.post(url, headers=headers, json=payload)
        _ = r.raise_for_status()

        raw = cast(object, r.json())
        if not isinstance(raw, dict):
            raise TypeError("Expected JSON object from Mistral API")

        choices = cast(list[dict[str, object]], raw["choices"])
        message = cast(dict[str, object], choices[0]["message"])
        content = message["content"]
        tool_calls = cast(list[dict[str, object]] | None, message.get("tool_calls"))

        tool_messages: list[dict[str, object]] = []
        if tools is not None and tool_calls is not None:
            allowed_functions = {t.name: t for t in tools}
            for c in tool_calls:
                if c["type"] != "function":
                    continue
                function = cast(dict[str, str], c["function"])
                name = function["name"]
                if name not in allowed_functions:
                    continue
                args = cast(dict[str, object], json.loads(function["arguments"]))
                fn = allowed_functions[name]
                value = fn.fn(**args)
                tool_messages.append(
                    {
                        "role": "tool",
                        "name": name,
                        "tool_call_id": c["id"],
                        "content": json.dumps(value),
                    }
                )

        assistant_response: dict[str, object] = {}
        if content is not None or tool_calls is not None:
            assistant_response = {
                "role": "assistant",
                "content": content,
            }
            if "tool_calls" in message:
                assistant_response["tool_calls"] = tool_calls

        return assistant_response, tool_messages

    async def chat(
        self, messages: list[dict[str, object]], tools: list[Tool] | None
    ) -> Chat:

        new_messages = messages

        assistant_response, tool_messages = await self._chat_one_turn(messages, tools)

        if assistant_response:
            new_messages = new_messages + [assistant_response]
        remaining_tool_call_rounds = 5
        while remaining_tool_call_rounds > 0 and tool_messages:
            new_messages = new_messages + tool_messages
            assistant_response, tool_messages = await self._chat_one_turn(
                new_messages, tools
            )
            new_messages = new_messages + [assistant_response]
            remaining_tool_call_rounds -= 1

        if tool_messages:
            raise RuntimeError("Maximum tool-calling rounds exceeded")

        return Chat(self, new_messages, tools)


class Chat:
    def __init__(
        self,
        client: MistralCompletionsClient,
        messages: list[dict[str, object]],
        tools: list[Tool] | None,
    ):
        self.client: MistralCompletionsClient = client
        self.messages: list[dict[str, object]] = messages
        self.tools: list[Tool] | None = tools

    async def chat(self, prompt: str) -> Chat:
        new_messages: list[dict[str, object]] = self.messages + [
            {"role": "user", "content": prompt}
        ]
        return await self.client.chat(new_messages, self.tools)


class Tool:
    def __init__(self, name: str, fn: Callable[..., object], meta: object):
        self.name: str = name
        self.fn: Callable[..., object] = fn
        self.meta: object = meta
