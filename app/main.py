import asyncio
import os

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


async def multiturn_tool_chat(client: MistralCompletionsClient) -> None:
    print("turn1")
    chat0 = await client.start_chat(
        "Calculate the percentage increase from 120 to 150 using the tool.",
        [tool_calculate_percentage_change],
    )
    print(chat0.messages)
    print("turn2")
    chat01 = await chat0.chat(
        "Now calculate the percentage increase from 150 to 210 using the same tool."
    )
    print(chat01.messages)
    print("turn3")
    chat02 = await chat01.chat(
        "Which of these two increases was larger, and by how many percentage points?"
    )
    print(chat02.messages)


async def main() -> None:
    filing_retriever = FilingRetriever()
    async with (
        EdgarAPI(edgar_api_user_agent) as edgar,
        MistralCompletionsClient(mistral_api_key) as client,
    ):
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

        # chat1 = await chat0.chat("What risks does Microsoft identify related to artificial intelligence?")
        # print(chat1.messages)


"""
    async with MistralCompletionsClient(mistral_api_key) as client:
        #        prompt = "What's the percentage increase from 120 to 150?"
        # prompt = "Calculate the percentage changes from 100 to 120, from 150 to 180, and from 200 to 250. Use the calculation tool for each, then compare the results."
        # prompt = "First, use the tool to calculate the percentage change from 120 to 150. Then take the percentage returned by the tool and use it as the old value for another percentage change calculation, with 50 as the new value. Use the tool for both calculations."
        # await multiturn_tool_chat(client)

        #chat0 = await client.start_chat(
        #    "What was Microsoft's revenue and operating income in fiscal year 2023?",
        #    [tool_get_company_financials],
        #)
        #print(chat0.messages)


#        chat1 = await client.start_chat("hello, world!", None)
#        print(chat1.messages)

#        chat2 = await chat1.chat("who is james bond?")
#        print(chat2.messages)
"""

if __name__ == "__main__":
    asyncio.run(main())
