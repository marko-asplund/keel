import json
from pathlib import Path
from typing import Self, TypedDict, cast

import httpx


class Ticker(TypedDict):
    cik_str: int
    ticker: str
    title: str


class EdgarAPI:
    def __init__(self, user_agent: str):
        self._included_concepts: set[str] = {
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "OperatingIncomeLoss",
        }
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=5.0)
        self._user_agent: str = user_agent
        self._request_headers: dict[str, str] = {
            "User-Agent": user_agent,
            "Accept": "application/json",
        }

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    async def _fetch_tickers(self) -> httpx.Response:
        r = await self._client.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=self._request_headers,
        )
        _ = r.raise_for_status()

        return r

    async def _get_tickers(self) -> dict[str, Ticker]:
        tickers_file = Path("cache/tickers.json")
        tickers: dict[str, Ticker]
        if tickers_file.is_file():
            text = tickers_file.read_text()
            tickers = cast(dict[str, Ticker], json.loads(text))
        else:
            r = await self._fetch_tickers()
            _ = tickers_file.write_text(r.text)
            tickers = cast(dict[str, Ticker], r.json())
        return {t["ticker"]: t for t in tickers.values()}

    async def get_company_financials(
        self, ticker: str, start_year: int, end_year: int
    ) -> object:
        by_ticker = await self._get_tickers()
        ticker_data = by_ticker.get(ticker)
        if ticker_data is None:
            raise ValueError(f"Ticker {ticker} not found")
        cik = int(ticker_data["cik_str"])
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

        r = await self._client.get(
            url,
            headers=self._request_headers,
        )
        _ = r.raise_for_status()

        data = cast(dict[str, object], r.json())
        facts = cast(dict[str, object], data["facts"])
        gaap = cast(dict[str, dict[str, object]], facts["us-gaap"])

        for concept in list(gaap):
            if concept not in self._included_concepts:
                del gaap[concept]
                continue
            units = cast(dict[str, list[dict[str, object]]], gaap[concept]["units"])
            for unit, observations in units.items():
                units[unit] = [
                    obs
                    for obs in observations
                    if start_year <= int(cast(str, obs["end"])[:4]) <= end_year
                ]

        data["facts"] = {"us-gaap": gaap}

        return data
