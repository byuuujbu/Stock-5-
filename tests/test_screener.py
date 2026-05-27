from __future__ import annotations

from app.models import Article, StockQuote
from app.screener import Screener


class MarketProvider:
    def fetch_quotes(self):
        return [
            StockQuote("KOSPI", "A", "A Corp", 1000, 5.0, 1_0000_0000_0000),
            StockQuote("KOSPI", "B", "B Corp", 1000, 4.99, 2_0000_0000_0000),
            StockQuote("KOSDAQ", "C", "C Corp", 1000, 7.0, 9000_0000_0000),
            StockQuote("KOSDAQ", "D", "D Corp", 1000, 9.0, 3_0000_0000_0000),
            StockQuote("KOSPI", "E", "E Corp", 1000, 8.0, 4_0000_0000_0000),
        ]


class FinancialProvider:
    def operating_profits(self, ticker):
        return {
            "A": [1, 2, 3],
            "B": [1, 2, 3],
            "C": [1, 2, 3],
            "D": [1, -1, 3],
            "E": [1, 2, -3],
        }.get(ticker, [])


class NewsProvider:
    def recent_articles(self, ticker, name):
        return [Article(f"{name} news", "https://example.com", "example", "2026-05-27")]


def test_screener_applies_all_filters():
    selected = Screener(MarketProvider(), FinancialProvider(), NewsProvider()).run()

    assert [(stock.ticker, stock.profit_tier) for stock in selected] == [("A", "3Y"), ("E", "2Y"), ("D", "1Y")]
    assert selected[0].articles[0].title == "A Corp news"


def test_screener_sorts_by_trading_value_and_caps_results():
    class ManyMarketProvider:
        def fetch_quotes(self):
            return [
                StockQuote("KOSPI", str(index), f"Corp {index}", 1000, 5.1, (index + 1) * 1_0000_0000_0000)
                for index in range(12)
            ]

    class PassingFinancialProvider:
        def operating_profits(self, ticker):
            return [1, 1, 1]

    selected = Screener(ManyMarketProvider(), PassingFinancialProvider(), NewsProvider()).run()

    assert len(selected) == 10
    assert [stock.ticker for stock in selected[:3]] == ["11", "10", "9"]
