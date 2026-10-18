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


def get_company_financials(
    ticker: str, start_year: int, end_year: int
) -> dict[str, object]:
    return {
        "ticker": "MSFT",
        "source": "mock",
        "currency": "USD",
        "annual": [
            {
                "fiscal_year": 2023,
                "revenue": 100_000_000_000,
                "operating_income": 40_000_000_000,
            },
        ],
    }


tool_get_company_financials: Tool = Tool(
    "get_company_financials",
    get_company_financials,
    {
        "type": "function",
        "function": {
            "name": "get_company_financials",
            "description": (
                "Retrieve historical annual revenue and operating "
                "income for a publicly traded company. "
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
    },
)
