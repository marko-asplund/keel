from __future__ import annotations
import httpx

class MistralCompletionsClient:
    _mistral_api_base_url: str = "https://api.mistral.ai"
    _default_model_name:str = "mistral-small-latest"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def start_chat(self, prompt: str) -> Chat:
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages)

    def chat(self, messages: list[dict]) -> Chat:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._default_model_name,
            "messages": messages
        }
        url = f"{self._mistral_api_base_url}/v1/chat/completions"
        r = httpx.post(url, headers=headers, json=payload)
        r.raise_for_status()

        json = r.json()
        if not isinstance(json, dict):
            raise ValueError(f"Expected JSON object, got {type(json).__name__}")

        assistant_response = json['choices'][0]['message']
        return Chat(self, messages + [assistant_response])

class Chat:
    def __init__(self, client: MistralCompletionsClient, messages: list[dict]):
        self.client = client
        self.messages = messages

    def chat(self, prompt: str) -> Chat:
        new_messages = self.messages + [{"role": "user", "content": prompt}]
        return self.client.chat(new_messages)
