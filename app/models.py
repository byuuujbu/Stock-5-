from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StockQuote:
    market: str
    ticker: str
    name: str
    close_price: int
    change_rate: float
    trading_value: int


@dataclass(frozen=True)
class Article:
    title: str
    link: str
    source: str
    published_at: str


@dataclass
class SelectedStock:
    market: str
    ticker: str
    name: str
    close_price: int
    change_rate: float
    trading_value: int
    operating_profits: list[int]
    profit_tier: str
    articles: list[Article] = field(default_factory=list)


@dataclass(frozen=True)
class IpoItem:
    company_name: str
    market: str
    status: str
    subscription_start: str
    subscription_end: str
    listing_date: str
    price_min: int | None
    price_max: int | None
    final_price: int | None
    lead_managers: str
    source_url: str
    official_url: str
