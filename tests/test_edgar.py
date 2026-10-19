import json
from pathlib import Path

import httpx
import pytest

from app.edgar import EdgarAPI


@pytest.fixture
def ticker_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / "cache"
    cache.mkdir()
    path = cache / "tickers.json"
    _ = path.write_text(
        json.dumps({"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple"}})
    )
    return path


# Keep only requested concepts and inclusive years while preserving metadata.
@pytest.mark.anyio
async def test_financials_filter_concepts_and_years(ticker_cache: Path) -> None:
    observations = [
        {"end": f"{year}-09-30", "val": year, "form": "10-K"}
        for year in [2022, 2023, 2024, 2025]
    ]
    revenue = "RevenueFromContractWithCustomerExcludingAssessedTax"
    data: dict[str, object] = {
        "cik": 320193,
        "entityName": "Apple",
        "facts": {
            "us-gaap": {
                concept: {"label": concept, "units": {"USD": observations}}
                for concept in [revenue, "OperatingIncomeLoss", "Assets"]
            },
            "dei": {"unrelated": {}},
        },
    }
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=data)

    async with EdgarAPI("Test test@example.com") as edgar:
        edgar._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # pyright: ignore[reportPrivateUsage]
        result = await edgar.get_company_financials("AAPL", 2023, 2024)

    assert result == {
        "cik": 320193,
        "entityName": "Apple",
        "facts": {
            "us-gaap": {
                concept: {"label": concept, "units": {"USD": observations[1:3]}}
                for concept in [revenue, "OperatingIncomeLoss"]
            }
        },
    }
    assert len(requests) == 1
    assert requests[0].url.path == "/api/xbrl/companyfacts/CIK0000320193.json"
    assert requests[0].headers["User-Agent"] == "Test test@example.com"
    assert ticker_cache.is_file()


# Unknown tickers fail before any financial-data request is sent.
@pytest.mark.anyio
async def test_unknown_ticker_does_not_request_financials(ticker_cache: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail(f"Unexpected request: {request.url}")

    async with EdgarAPI("Test test@example.com") as edgar:
        edgar._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # pyright: ignore[reportPrivateUsage]
        with pytest.raises(ValueError, match="Ticker UNKNOWN not found"):
            _ = await edgar.get_company_financials("UNKNOWN", 2023, 2024)
    assert ticker_cache.is_file()


# SEC HTTP failures propagate to the caller.
@pytest.mark.anyio
async def test_financials_http_error(ticker_cache: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with EdgarAPI("Test test@example.com") as edgar:
        edgar._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # pyright: ignore[reportPrivateUsage]
        with pytest.raises(httpx.HTTPStatusError):
            _ = await edgar.get_company_financials("AAPL", 2023, 2024)
    assert ticker_cache.is_file()
