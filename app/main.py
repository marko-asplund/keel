import asyncio
import os

from dotenv import load_dotenv

from app.mistral_chat import MistralCompletionsClient, Tool

_ = load_dotenv()
mistral_api_key: str = str(os.getenv("MISTRAL_API_KEY"))


def calculate_percentage_change(old: float, new: float) -> float:
    return (new - old) / old * 100


tool_calculate_percentage_change: Tool = Tool(
    "calculate_percentage_change",
    calculate_percentage_change,
    {
        "type": "function",
        "function": {
            "name": "calculate_percentage_change",
            "description": "Calculate the percentage change between two values",
            "parameters": {
                "type": "object",
                "properties": {"old": {"type": "number"}, "new": {"type": "number"}},
                "required": ["old", "new"],
            },
        },
    },
)

tools: list[Tool] = [tool_calculate_percentage_change]


async def main() -> None:
    async with MistralCompletionsClient(mistral_api_key) as client:
        chat0 = await client.start_chat(
            "What's the percentage increase from 120 to 150?", tools
        )
        print(chat0.messages)


#        chat1 = await client.start_chat("hello, world!", None)
#        print(chat1.messages)

#        chat2 = await chat1.chat("who is james bond?")
#        print(chat2.messages)


if __name__ == "__main__":
    asyncio.run(main())
