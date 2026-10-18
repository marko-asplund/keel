from __future__ import annotations

from collections.abc import Callable
from typing import Self

import httpx
import json


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

    async def start_chat(self, prompt: str, tools: list[Tool] | None) -> Chat:
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        return await self.chat(messages, tools)

    async def chat(
        self, messages: list[dict[str, str]], tools: list[Tool] | None
    ) -> Chat:
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

        raw = r.json()  # pyright: ignore[reportAny]
        if not isinstance(raw, dict):
            raise TypeError("Expected JSON object from Mistral API")

        message = raw["choices"][0]["message"]  # pyright: ignore[reportUnknownVariableType]
        print(message)
        content = message["content"]
        tool_calls = message["tool_calls"]

        if tools is not None:
            allowed_functions = {t.name: t for t in tools}
            allowed_calls = filter(
                lambda t: (
                    t["type"] == "function"
                    and t["function"]["name"] in allowed_functions
                ),
                tool_calls,
            )
            for c in allowed_calls:
                args = json.loads(c["function"]["arguments"])
                fn = allowed_functions[c["function"]["name"]]
                value = fn.fn(**args)
                print(f"c: {c} -- {args} -- {value}")

        if not isinstance(content, str):
            raise TypeError("Expected text content from Mistral API")

        assistant_response: dict[str, str] = {"role": "assistant", "content": content}
        return Chat(self, messages + [assistant_response], tools)


class Chat:
    def __init__(
        self,
        client: MistralCompletionsClient,
        messages: list[dict[str, str]],
        tools: list[Tool] | None,
    ):
        self.client: MistralCompletionsClient = client
        self.messages: list[dict[str, str]] = messages
        self.tools: list[Tool] | None = tools

    async def chat(self, prompt: str) -> Chat:
        new_messages: list[dict[str, str]] = self.messages + [
            {"role": "user", "content": prompt}
        ]
        return await self.client.chat(new_messages, self.tools)


class Tool:
    def __init__(self, name: str, fn: Callable[..., ...], meta: object):
        self.name = name
        self.fn = fn
        self.meta = meta
