from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.models import Article, IpoItem, SelectedStock


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_date TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS selections (
    run_date TEXT NOT NULL,
    rank INTEGER NOT NULL,
    market TEXT NOT NULL,
    ticker TEXT NOT NULL,
    name TEXT NOT NULL,
    close_price INTEGER NOT NULL,
    change_rate REAL NOT NULL,
    trading_value INTEGER NOT NULL,
    operating_profits_json TEXT NOT NULL,
    profit_tier TEXT NOT NULL DEFAULT '3Y',
    PRIMARY KEY (run_date, ticker)
);

CREATE TABLE IF NOT EXISTS articles (
    run_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT NOT NULL,
    PRIMARY KEY (run_date, ticker, link)
);

CREATE TABLE IF NOT EXISTS ipos (
    run_date TEXT NOT NULL,
    company_name TEXT NOT NULL,
    market TEXT NOT NULL,
    status TEXT NOT NULL,
    subscription_start TEXT NOT NULL,
    subscription_end TEXT NOT NULL,
    listing_date TEXT NOT NULL,
    price_min INTEGER,
    price_max INTEGER,
    final_price INTEGER,
    lead_managers TEXT NOT NULL,
    source_url TEXT NOT NULL,
    official_url TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (run_date, company_name, subscription_start)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(ipos)").fetchall()}
    if "official_url" not in columns:
        conn.execute("ALTER TABLE ipos ADD COLUMN official_url TEXT NOT NULL DEFAULT ''")
    selection_columns = {row["name"] for row in conn.execute("PRAGMA table_info(selections)").fetchall()}
    if "profit_tier" not in selection_columns:
        conn.execute("ALTER TABLE selections ADD COLUMN profit_tier TEXT NOT NULL DEFAULT '3Y'")


def save_run(db_path: Path, run_date: str, mode: str, stocks: list[SelectedStock], ipos: list[IpoItem] | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO runs(run_date, created_at, mode) VALUES (?, datetime('now'), ?)",
            (run_date, mode),
        )
        conn.execute("DELETE FROM selections WHERE run_date = ?", (run_date,))
        conn.execute("DELETE FROM articles WHERE run_date = ?", (run_date,))
        conn.execute("DELETE FROM ipos WHERE run_date = ?", (run_date,))
        for rank, stock in enumerate(stocks, start=1):
            conn.execute(
                """
                INSERT INTO selections(
                    run_date, rank, market, ticker, name, close_price, change_rate,
                    trading_value, operating_profits_json, profit_tier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_date,
                    rank,
                    stock.market,
                    stock.ticker,
                    stock.name,
                    stock.close_price,
                    stock.change_rate,
                    stock.trading_value,
                    json.dumps(stock.operating_profits, ensure_ascii=False),
                    stock.profit_tier,
                ),
            )
            for article in stock.articles:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO articles(
                        run_date, ticker, title, link, source, published_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (run_date, stock.ticker, article.title, article.link, article.source, article.published_at),
                )
        for ipo in ipos or []:
            _insert_ipo(conn, run_date, ipo)


def save_ipos(db_path: Path, run_date: str, ipos: list[IpoItem]) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM ipos WHERE run_date = ?", (run_date,))
        for ipo in ipos:
            _insert_ipo(conn, run_date, ipo)


def _insert_ipo(conn: sqlite3.Connection, run_date: str, ipo: IpoItem) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO ipos(
            run_date, company_name, market, status, subscription_start, subscription_end,
            listing_date, price_min, price_max, final_price, lead_managers, source_url, official_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_date,
            ipo.company_name,
            ipo.market,
            ipo.status,
            ipo.subscription_start,
            ipo.subscription_end,
            ipo.listing_date,
            ipo.price_min,
            ipo.price_max,
            ipo.final_price,
            ipo.lead_managers,
            ipo.source_url,
            ipo.official_url,
        ),
    )


def latest_run_date(db_path: Path) -> str | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT run_date FROM runs ORDER BY run_date DESC LIMIT 1").fetchone()
        return row["run_date"] if row else None


def list_runs(db_path: Path) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT r.run_date, r.created_at, r.mode, COUNT(s.ticker) AS stock_count
            FROM runs r
            LEFT JOIN selections s ON s.run_date = r.run_date
            GROUP BY r.run_date, r.created_at, r.mode
            ORDER BY r.run_date DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def load_run(db_path: Path, run_date: str | None = None) -> tuple[str | None, list[dict[str, Any]]]:
    target_date = run_date or latest_run_date(db_path)
    if not target_date:
        return None, []
    with connect(db_path) as conn:
        stock_rows = conn.execute(
            "SELECT * FROM selections WHERE run_date = ? ORDER BY rank ASC",
            (target_date,),
        ).fetchall()
        article_rows = conn.execute(
            "SELECT * FROM articles WHERE run_date = ? ORDER BY ticker, published_at DESC",
            (target_date,),
        ).fetchall()
    articles_by_ticker: dict[str, list[dict[str, Any]]] = {}
    for row in article_rows:
        articles_by_ticker.setdefault(row["ticker"], []).append(dict(row))
    stocks = []
    for row in stock_rows:
        item = dict(row)
        item["operating_profits"] = json.loads(item.pop("operating_profits_json"))
        item["articles"] = articles_by_ticker.get(item["ticker"], [])
        stocks.append(item)
    return target_date, stocks


def load_ipos(db_path: Path, run_date: str | None = None) -> tuple[str | None, list[dict[str, Any]]]:
    target_date = run_date or latest_run_date(db_path)
    if not target_date:
        return None, []
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM ipos
            WHERE run_date = ?
            ORDER BY COALESCE(NULLIF(subscription_start, ''), listing_date), company_name
            """,
            (target_date,),
        ).fetchall()
        return target_date, [dict(row) for row in rows]
