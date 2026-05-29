from __future__ import annotations

import csv
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.models import StockQuote
from app.utils import http_json, read_json, write_json


KST = timezone(timedelta(hours=9))


class RateLimiter:
    def __init__(self, min_interval_seconds: float):
        self.min_interval_seconds = min_interval_seconds
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        remaining = self.min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_call = time.monotonic()


class KisMarketDataProvider:
    def __init__(
        self,
        base_url: str,
        app_key: str,
        app_secret: str,
        universe_csv: Path,
        *,
        min_interval_seconds: float = 0.12,
        token_cache_path: Path | None = None,
        token_retry_wait_seconds: float = 65.0,
        token_max_attempts: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.app_key = app_key
        self.app_secret = app_secret
        self.universe_csv = universe_csv
        self.rate_limiter = RateLimiter(min_interval_seconds)
        self.token_cache_path = token_cache_path
        self.token_retry_wait_seconds = token_retry_wait_seconds
        self.token_max_attempts = max(1, token_max_attempts)
        self._access_token: str | None = None

    def fetch_quotes(self) -> list[StockQuote]:
        rows = self._load_universe()
        quotes: list[StockQuote] = []
        for row in rows:
            quote = self._fetch_quote(row)
            if quote is not None:
                quotes.append(quote)
        return quotes

    def _load_universe(self) -> list[dict[str, str]]:
        path = self.universe_csv
        if not path.exists():
            sample = Path("data/universe.sample.csv")
            raise FileNotFoundError(
                f"KIS universe CSV not found: {path}. Copy {sample} to {path} and maintain KOSPI/KOSDAQ tickers."
            )
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        required = {"market", "ticker", "name"}
        if not rows or not required.issubset(rows[0].keys()):
            raise ValueError("KIS universe CSV must include market,ticker,name columns.")
        return rows

    def _token(self) -> str:
        if self._access_token:
            return self._access_token
        cached = self._read_cached_token()
        if cached:
            self._access_token = cached
            return cached
        payload = {"grant_type": "client_credentials", "appkey": self.app_key, "appsecret": self.app_secret}
        data = self._request_new_token(payload)
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"KIS token response missing access_token: {data}")
        self._access_token = token
        self._write_cached_token(token, data)
        return token

    def _request_new_token(self, payload: dict[str, str]) -> dict[str, Any]:
        last_error: RuntimeError | None = None
        for attempt in range(self.token_max_attempts):
            try:
                return http_json(f"{self.base_url}/oauth2/tokenP", method="POST", body=payload)
            except RuntimeError as exc:
                message = str(exc)
                if "EGW00133" not in message and "1분당 1회" not in message:
                    raise
                last_error = exc
                if attempt < self.token_max_attempts - 1:
                    time.sleep(self.token_retry_wait_seconds)
        if last_error is not None:
            raise last_error
        raise RuntimeError("KIS token request failed without an error.")

    def _read_cached_token(self) -> str | None:
        if self.token_cache_path is None:
            return None
        data = read_json(self.token_cache_path, default={})
        token = data.get("access_token")
        expires_at = data.get("expires_at")
        if not token or not expires_at:
            return None
        try:
            expiry = datetime.fromisoformat(expires_at)
        except ValueError:
            return None
        if datetime.now(tz=KST) >= expiry:
            return None
        return str(token)

    def _write_cached_token(self, token: str, data: dict[str, Any]) -> None:
        if self.token_cache_path is None:
            return
        expires_in = _to_int(data.get("expires_in")) or 60 * 60 * 23
        expires_at = datetime.now(tz=KST) + timedelta(seconds=max(60, expires_in - 300))
        write_json(
            self.token_cache_path,
            {"access_token": token, "expires_at": expires_at.isoformat()},
        )

    def _fetch_quote(self, row: dict[str, str]) -> StockQuote | None:
        ticker = row["ticker"].strip()
        self.rate_limiter.wait()
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self._token()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST03010100",
            "custtype": "P",
        }
        today = datetime.now(tz=KST).date()
        start = (today - timedelta(days=14)).strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_INPUT_DATE_1": start,
            "FID_INPUT_DATE_2": end,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "1",
        }
        try:
            data = http_json(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                params=params,
                headers=headers,
            )
        except RuntimeError:
            return None
        candles = _sorted_candles(data.get("output2") or [])
        if len(candles) < 2:
            return None
        latest = candles[-1]
        previous = candles[-2]
        close_price = _to_int(latest.get("stck_clpr"))
        previous_close = _to_int(previous.get("stck_clpr"))
        if close_price <= 0 or previous_close <= 0:
            return None
        trading_value = _to_int(latest.get("acml_tr_pbmn"))
        if trading_value <= 0:
            trading_value = close_price * _to_int(latest.get("acml_vol"))
        return StockQuote(
            market=row.get("market", "").strip(),
            ticker=ticker,
            name=_name_from_response(data, row),
            close_price=close_price,
            change_rate=((close_price - previous_close) / previous_close) * 100,
            trading_value=trading_value,
        )


def _sorted_candles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [row for row in rows if row.get("stck_bsop_date")],
        key=lambda row: str(row.get("stck_bsop_date")),
    )


def _name_from_response(data: dict[str, Any], row: dict[str, str]) -> str:
    output1 = data.get("output1") or {}
    return output1.get("hts_kor_isnm") or row.get("name", "").strip()


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(str(value).replace(",", "").strip())
