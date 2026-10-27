import argparse
import asyncio
import os
from typing import cast

from dotenv import load_dotenv

from app.edgar import EdgarAPI
from app.filing_retriever import FilingRetriever
from app.mistral_chat import MistralCompletionsClient, Tool
from app.tools import (
    get_company_financials_tool_schema,
    search_filings_tool_schema,
    tool_calculate_percentage_change,
)

_ = load_dotenv()
mistral_api_key: str = str(os.getenv("MISTRAL_API_KEY"))
edgar_api_user_agent: str = str(os.getenv("EDGAR_API_USER_AGENT"))


async def demo_hello_world(client: MistralCompletionsClient) -> None:
    chat = await client.start_chat("hello, world!")
    print(chat.messages)


async def demo_simple_tool_call(client: MistralCompletionsClient) -> None:
    chat = await client.start_chat(
        "Calculate the percentage increase from 120 to 150 using the tool.",
        [tool_calculate_percentage_change],
    )
    print(chat.messages)


# multiturn simple tool call
async def demo_multiturn_tool_chat(client: MistralCompletionsClient) -> None:
    print("turn1")
    chat0 = await client.start_chat(
        "Calculate the percentage increase from 120 to 150 using the tool.",
        [tool_calculate_percentage_change],
    )
    print(chat0.messages)
    print("turn2")
    chat1 = await chat0.chat(
        "Now calculate the percentage increase from 150 to 210 using the same tool."
    )
    print(chat1.messages)
    print("turn3")
    chat2 = await chat1.chat(
        "Which of these two increases was larger, and by how many percentage points?"
    )
    print(chat2.messages)


# chat with multiple tools
async def demo_financials(
    client: MistralCompletionsClient, edgar: EdgarAPI, filing_retriever: FilingRetriever
) -> None:
    search_filings_tool_schema_tool = Tool(
        "search_filings", filing_retriever.retrieve, search_filings_tool_schema
    )
    get_company_financials_tool = Tool(
        "get_company_financials",
        edgar.get_company_financials,
        get_company_financials_tool_schema,
    )

    print("chat0")
    chat0 = await client.start_chat(
        "Did Microsoft's operating margin improve between FY2023 and FY2025?",
        [get_company_financials_tool, search_filings_tool_schema_tool],
    )
    print(chat0.messages)

    print("chat1")
    chat1 = await client.start_chat(
        "What risks does Microsoft identify related to artificial intelligence?",
        [search_filings_tool_schema_tool],
    )
    print(chat1.messages)


async def main() -> None:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("demo_choice", type=str)
    args = parser.parse_args()

    async with (
        EdgarAPI(edgar_api_user_agent) as edgar,
        MistralCompletionsClient(mistral_api_key) as client,
    ):
        choice: str = cast(str, args.demo_choice)
        if choice == "hello_world":
            await demo_hello_world(client)
        elif choice == "simple_tool_call":
            await demo_simple_tool_call(client)
        elif choice == "multiturn":
            await demo_multiturn_tool_chat(client)
        elif choice == "financials":
            filing_retriever = FilingRetriever()
            await demo_financials(client, edgar, filing_retriever)
        else:
            raise ValueError(f"Unknown demo choice {choice}")


if __name__ == "__main__":
    asyncio.run(main())
