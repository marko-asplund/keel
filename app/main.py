import asyncio
import os

from dotenv import load_dotenv

from app.mistral_chat import MistralCompletionsClient

_ = load_dotenv()
mistral_api_key: str = str(os.getenv("MISTRAL_API_KEY"))


async def main() -> None:
    async with MistralCompletionsClient(mistral_api_key) as client:
        chat1 = await client.start_chat("hello, world!")

        print(chat1.messages)

        chat2 = await chat1.chat("who is james bond?")

        print(chat2.messages)


if __name__ == "__main__":
    asyncio.run(main())
