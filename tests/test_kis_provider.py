from __future__ import annotations

from app.providers.kis import _sorted_candles


def test_sorted_candles_orders_by_business_date():
    rows = [
        {"stck_bsop_date": "20260527", "stck_clpr": "1100"},
        {"stck_bsop_date": "20260524", "stck_clpr": "1000"},
        {"stck_clpr": "999"},
    ]

    assert [row["stck_bsop_date"] for row in _sorted_candles(rows)] == ["20260524", "20260527"]

