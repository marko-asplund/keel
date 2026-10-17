import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class MistralCompletionsClient:
    _mistral_api_base_url: str = "https://api.mistral.ai"
    _default_model_name:str = "mistral-small-latest"

    def __init__(self, api_key):
        self._api_key = api_key

    def start_chat(self, prompt: str):
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages)

    def chat(self, messages):
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
        json = r.json()

        assistant_response = json['choices'][0]['message']
        return Chat(self, messages + [assistant_response])

class Chat:
    def __init__(self, client, messages):
        self.client = client
        self.messages = messages

    def chat(self, prompt: str):
        new_messages = self.messages + [{"role": "user", "content": prompt}]
        return self.client.chat(new_messages)


client = MistralCompletionsClient(os.getenv("MISTRAL_API_KEY"))

chat1 = client.start_chat("hello, world!")

print(chat1.messages)

chat2 = chat1.chat("who is james bond?")

print(chat2.messages)