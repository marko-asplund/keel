import os

from dotenv import load_dotenv

from app.mistral_chat import MistralCompletionsClient

_ = load_dotenv()

client = MistralCompletionsClient(str(os.getenv("MISTRAL_API_KEY")))

chat1 = client.start_chat("hello, world!")

print(chat1.messages)

chat2 = chat1.chat("who is james bond?")

print(chat2.messages)