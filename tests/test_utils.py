from __future__ import annotations

from app.utils import money_krw


def test_money_krw_formats_large_values():
    assert money_krw(1_2300_0000_0000) == "1.23조"
    assert money_krw(4500_0000_0000) == "4500억"

