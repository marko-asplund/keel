from __future__ import annotations

from typing import Self

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

    async def start_chat(self, prompt: str) -> Chat:
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        return await self.chat(messages)

    async def chat(self, messages: list[dict[str, str]]) -> Chat:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {
            "model": self._default_model_name,
            "messages": messages,
        }
        url = f"{self._mistral_api_base_url}/v1/chat/completions"
        r = await self._client.post(url, headers=headers, json=payload)
        _ = r.raise_for_status()

        raw = r.json()  # pyright: ignore[reportAny]
        if not isinstance(raw, dict):
            raise TypeError("Expected JSON object from Mistral API")

        content = raw["choices"][0]["message"]["content"]  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(content, str):
            raise TypeError("Expected text content from Mistral API")
        assistant_response: dict[str, str] = {"role": "assistant", "content": content}
        return Chat(self, messages + [assistant_response])


class Chat:
    def __init__(
        self, client: MistralCompletionsClient, messages: list[dict[str, str]]
    ):
        self.client: MistralCompletionsClient = client
        self.messages: list[dict[str, str]] = messages

    async def chat(self, prompt: str) -> Chat:
        new_messages: list[dict[str, str]] = self.messages + [
            {"role": "user", "content": prompt}
        ]
        return await self.client.chat(new_messages)
