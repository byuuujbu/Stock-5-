from __future__ import annotations

from app.db import list_runs, load_run, save_run
from app.models import Article, SelectedStock


def _stock(ticker: str, article_title: str) -> SelectedStock:
    return SelectedStock(
        market="KOSPI",
        ticker=ticker,
        name=f"{ticker} Corp",
        close_price=1000,
        change_rate=5.5,
        trading_value=1_0000_0000_0000,
        operating_profits=[1, 2, 3],
        profit_tier="3Y",
        articles=[Article(article_title, f"https://example.com/{ticker}", "example", "2026-05-27")],
    )


def test_save_run_replaces_same_date(tmp_path):
    db_path = tmp_path / "agent.sqlite3"

    save_run(db_path, "2026-05-27", "sample", [_stock("A", "old")])
    save_run(db_path, "2026-05-27", "sample", [_stock("B", "new")])

    run_date, stocks = load_run(db_path)

    assert run_date == "2026-05-27"
    assert [stock["ticker"] for stock in stocks] == ["B"]
    assert stocks[0]["articles"][0]["title"] == "new"


def test_history_keeps_zero_selection_run(tmp_path):
    db_path = tmp_path / "agent.sqlite3"

    save_run(db_path, "2026-05-27", "real", [])

    runs = list_runs(db_path)

    assert runs == [
        {
            "run_date": "2026-05-27",
            "created_at": runs[0]["created_at"],
            "mode": "real",
            "stock_count": 0,
        }
    ]
