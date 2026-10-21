import argparse
import os

import httpx
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description="Load SEC filings")
parser.add_argument("ticker", type=str)
parser.add_argument("--year", type=int, nargs="+", required=True)

args = parser.parse_args()

_ = load_dotenv()

EDGAR_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_SUBMISSIONS_BASE_URL = "https://data.sec.gov/submissions"
EDGAR_DOC_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

edgar_api_user_agent: str = str(os.getenv("EDGAR_API_USER_AGENT"))
headers = {"User-Agent": edgar_api_user_agent}

client = httpx.Client(headers=headers)

res = client.get(EDGAR_TICKERS_URL)
res.raise_for_status()
all_tickers = res.json()
if len(all_tickers) < 100:
    raise SystemExit("Failed to load stock tickers from Edgar API")

ticker = args.ticker.upper()
tickers = list(filter(lambda t: t["ticker"] == ticker, all_tickers.values()))
if len(tickers) != 1:
    raise SystemExit("Expecting exactly one matching ticker")

cik = int(tickers[0]["cik_str"])
submissions_url = f"{EDGAR_SUBMISSIONS_BASE_URL}/CIK{cik:010d}.json"

res = client.get(submissions_url)
res.raise_for_status()
data = res.json()

recent = data["filings"]["recent"]

filings = [
    (report_date, accession, document)
    for form, report_date, accession, document in zip(
        recent["form"],
        recent["reportDate"],
        recent["accessionNumber"],
        recent["primaryDocument"],
    )
    if form == "10-K" and int(report_date[:4]) in args.year
]
if len(filings) == 0:
    raise SystemExit("No filings found")
if len(filings) != len(args.year):
    raise SystemExit("Filings missing for some years")

for f in filings:
    accn = f[1].replace("-", "")
    src_fn = f[2]
    url = f"{EDGAR_DOC_BASE_URL}/{cik}/{accn}/{src_fn}"
    res = client.get(url)
    res.raise_for_status()

    year = int(f[0][:4])
    tgt_fn = f"{ticker}-{year}-10k.html"
    path = f"data/documents/{tgt_fn}"
    print(f"Writing doc {path}")
    with open(path, "wb") as file:
        file.write(res.content)
