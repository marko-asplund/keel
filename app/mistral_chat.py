from __future__ import annotations

from typing import cast

import httpx


class MistralCompletionsClient:
    _mistral_api_base_url: str = "https://api.mistral.ai"
    _default_model_name: str = "mistral-small-latest"

    def __init__(self, api_key: str):
        self._api_key: str = api_key

    def start_chat(self, prompt: str) -> Chat:
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        return self.chat(messages)

    def chat(self, messages: list[dict[str, str]]) -> Chat:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {"model": self._default_model_name, "messages": messages}
        url = f"{self._mistral_api_base_url}/v1/chat/completions"
        r = httpx.post(url, headers=headers, json=payload)
        _ = r.raise_for_status()

        raw = r.json()  # pyright: ignore[reportAny]
        if not isinstance(raw, dict):
            raise ValueError("Expected JSON object from Mistral API")

        assistant_response = cast(dict[str, str], raw["choices"][0]["message"])
        return Chat(self, messages + [assistant_response])


class Chat:
    def __init__(self, client: MistralCompletionsClient, messages: list[dict[str, str]]):
        self.client: MistralCompletionsClient = client
        self.messages: list[dict[str, str]] = messages

    def chat(self, prompt: str) -> Chat:
        new_messages: list[dict[str, str]] = self.messages + [{"role": "user", "content": prompt}]
        return self.client.chat(new_messages)