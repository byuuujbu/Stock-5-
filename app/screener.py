from __future__ import annotations

from collections import defaultdict

from app.models import SelectedStock, StockQuote


MIN_TRADING_VALUE = 1_0000_0000_0000
MIN_CHANGE_RATE = 5.0
MAX_SELECTIONS_PER_TIER = 10
PROFIT_TIERS = ("3Y", "2Y", "1Y")


class Screener:
    def __init__(self, market_provider, financial_provider, news_provider):
        self.market_provider = market_provider
        self.financial_provider = financial_provider
        self.news_provider = news_provider

    def run(self) -> list[SelectedStock]:
        quotes = self.market_provider.fetch_quotes()
        filtered = [
            quote
            for quote in quotes
            if quote.trading_value >= MIN_TRADING_VALUE and quote.change_rate >= MIN_CHANGE_RATE
        ]
        grouped: dict[str, list[SelectedStock]] = defaultdict(list)
        for quote in sorted(filtered, key=lambda item: item.trading_value, reverse=True):
            profits = self.financial_provider.operating_profits(quote.ticker)
            tier = profit_tier(profits)
            if tier is None:
                continue
            if len(grouped[tier]) >= MAX_SELECTIONS_PER_TIER:
                continue
            grouped[tier].append(_to_selected_stock(quote, profits, tier, self.news_provider))
        selected: list[SelectedStock] = []
        for tier in PROFIT_TIERS:
            selected.extend(grouped[tier])
        return selected


def profit_tier(profits: list[int]) -> str | None:
    if len(profits) >= 3 and all(value > 0 for value in profits[:3]):
        return "3Y"
    if len(profits) >= 2 and all(value > 0 for value in profits[:2]):
        return "2Y"
    if len(profits) >= 1 and profits[0] > 0:
        return "1Y"
    return None


def _to_selected_stock(quote: StockQuote, profits: list[int], tier: str, news_provider) -> SelectedStock:
    return SelectedStock(
        market=quote.market,
        ticker=quote.ticker,
        name=quote.name,
        close_price=quote.close_price,
        change_rate=quote.change_rate,
        trading_value=quote.trading_value,
        operating_profits=profits[:3],
        profit_tier=tier,
        articles=news_provider.recent_articles(quote.ticker, quote.name),
    )
