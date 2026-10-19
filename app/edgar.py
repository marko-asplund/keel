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
        self._included_concepts = {
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "OperatingIncomeLoss",
        }
        self._client = httpx.AsyncClient(timeout=5.0)
        self._user_agent = user_agent
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
        r.raise_for_status()

        return r

    async def _get_tickers(self):
        tickers_file = Path("cache/tickers.json")
        if tickers_file.is_file():
            text = tickers_file.read_text()
            tickers: dict[str, Ticker] = cast(dict[str, Ticker], json.loads(text))
        else:
            r = await self._fetch_tickers()
            tickers_file.write_text(r.text)
            tickers: dict[str, Ticker] = cast(dict[str, Ticker], r.json())
        return {t["ticker"]: t for t in tickers.values()}

    async def foo(self, ticker: str, start_year: int, end_year: int):
        by_ticker = await self._get_tickers()
        data = by_ticker[ticker]
        if not data:
            raise ValueError(f"Ticker {ticker} not found")
        cik = int(data["cik_str"])
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

        r = await self._client.get(
            url,
            headers=self._request_headers,
        )
        r.raise_for_status()

        data = r.json()
        gaap = data["facts"]["us-gaap"]

        for concept in list(gaap):
            if concept not in self._included_concepts:
                del gaap[concept]
                continue
            for unit, observations in gaap[concept]["units"].items():
                gaap[concept]["units"][unit] = [
                    obs
                    for obs in observations
                    if start_year <= int(obs["end"][:4]) <= end_year
                ]

        data["facts"] = {"us-gaap": gaap}

        return data
