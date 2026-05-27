from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path

import pandas as pd
import requests


OUTPUT_COLUMNS = ["market", "ticker", "name"]
KST = timezone(timedelta(hours=9))
KIND_LISTING_URL = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/universe.csv")
    parser.add_argument("--include-preferred", action="store_true")
    args = parser.parse_args()

    rows = []
    try:
        rows = _load_with_kind(args.include_preferred)
    except Exception as exc:
        print(f"KIND failed: {exc}")
        try:
            rows = _load_with_finance_datareader(args.include_preferred)
        except Exception as fallback_exc:
            print(f"FinanceDataReader failed: {fallback_exc}")
            rows = _load_with_pykrx(args.include_preferred)

    rows = sorted(_dedupe(rows), key=lambda row: (row["market"], row["ticker"]))
    if len(rows) < 1000:
        raise RuntimeError(f"Refusing to overwrite universe with only {len(rows)} rows.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} tickers to {output}")


def _dedupe(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for row in rows:
        key = (row["market"], row["ticker"])
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _looks_like_preferred_share(name: str) -> bool:
    return name.endswith("우") or "우B" in name or "우선주" in name


def _load_with_kind(include_preferred: bool) -> list[dict[str, str]]:
    response = requests.get(KIND_LISTING_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()
    text = response.content.decode("euc-kr", errors="replace")
    listings = pd.read_html(io.StringIO(text))[0]
    market_map = {"유가": "KOSPI", "코스닥": "KOSDAQ"}
    rows = []
    for _, item in listings.iterrows():
        market = market_map.get(str(item.get("시장구분", "")).strip())
        ticker = str(item.get("종목코드", "")).strip().zfill(6)
        name = str(item.get("회사명", "")).strip()
        if market is None:
            continue
        if not ticker.isdigit() or len(ticker) != 6:
            continue
        if _looks_like_spac(name):
            continue
        if _include(name, ticker, include_preferred):
            rows.append({"market": market, "ticker": ticker, "name": name})
    return rows


def _load_with_finance_datareader(include_preferred: bool) -> list[dict[str, str]]:
    import FinanceDataReader as fdr

    rows = []
    for market in ("KOSPI", "KOSDAQ"):
        listings = fdr.StockListing(market)
        for _, item in listings.iterrows():
            ticker = str(item.get("Code", "")).zfill(6)
            name = str(item.get("Name", "")).strip()
            if _include(name, ticker, include_preferred):
                rows.append({"market": market, "ticker": ticker, "name": name})
    return rows


def _load_with_pykrx(include_preferred: bool) -> list[dict[str, str]]:
    from pykrx import stock

    rows = []
    today = datetime.now(tz=KST).strftime("%Y%m%d")
    for market in ("KOSPI", "KOSDAQ"):
        tickers = stock.get_market_ticker_list(today, market=market)
        for ticker in tickers:
            name = stock.get_market_ticker_name(ticker)
            if _include(name, ticker, include_preferred):
                rows.append({"market": market, "ticker": ticker, "name": name})
    return rows


def _include(name: str, ticker: str, include_preferred: bool) -> bool:
    if not ticker or not name:
        return False
    if not include_preferred and _looks_like_preferred_share(name):
        return False
    return True


def _looks_like_spac(name: str) -> bool:
    compact = name.replace(" ", "")
    return "스팩" in compact or "기업인수목적" in compact


if __name__ == "__main__":
    main()
