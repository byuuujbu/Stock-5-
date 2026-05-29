from __future__ import annotations

from pathlib import Path

import app.providers.kis as kis_module
from app.providers.kis import _sorted_candles


def test_sorted_candles_orders_by_business_date():
    rows = [
        {"stck_bsop_date": "20260527", "stck_clpr": "1100"},
        {"stck_bsop_date": "20260524", "stck_clpr": "1000"},
        {"stck_clpr": "999"},
    ]

    assert [row["stck_bsop_date"] for row in _sorted_candles(rows)] == ["20260524", "20260527"]


def test_token_retries_kis_one_per_minute_error(monkeypatch):
    calls = []
    sleeps = []

    def fake_http_json(url, *, method="GET", body=None, **kwargs):
        calls.append((url, method, body))
        if len(calls) < 3:
            raise RuntimeError(
                "HTTP 403 from https://openapi.koreainvestment.com:9443/oauth2/tokenP: "
                '{"error_code":"EGW00133","error_description":"접근토큰 발급 잠시 후 다시 시도하세요(1분당 1회)"}'
            )
        return {"access_token": "token", "expires_in": 86400}

    monkeypatch.setattr(kis_module, "http_json", fake_http_json)
    monkeypatch.setattr(kis_module.time, "sleep", lambda seconds: sleeps.append(seconds))

    provider = kis_module.KisMarketDataProvider(
        "https://openapi.koreainvestment.com:9443",
        "app-key",
        "app-secret",
        Path("data/universe.csv"),
        token_retry_wait_seconds=0.01,
    )

    assert provider._token() == "token"
    assert len(calls) == 3
    assert sleeps == [0.01, 0.01]
