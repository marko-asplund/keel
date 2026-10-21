from app.mistral_chat import Tool


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


get_company_financials_tool_schema: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "get_company_financials",
        "description": (
            "Retrieve numeric revenue and operating income data from SEC EDGAR "
            "for a publicly traded company. Use for quantitative questions about "
            "these metrics, including growth, comparisons, and operating margins. "
            "Years refer to company fiscal years."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker, e.g. MSFT",
                },
                "start_year": {
                    "type": "integer",
                    "description": "First fiscal year",
                },
                "end_year": {
                    "type": "integer",
                    "description": "Last fiscal year",
                },
            },
            "required": ["ticker", "start_year", "end_year"],
        },
    },
}

search_filings_tool_schema: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "search_filings",
        "description": (
            "Search locally indexed SEC filings for a company and return relevant "
            "text passages with source filenames. Use for qualitative questions "
            "about disclosed risks, artificial intelligence, business strategy, "
            "and management commentary. Only downloaded and indexed filings "
            "are available."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "years": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["query", "years"],
        },
    },
}
