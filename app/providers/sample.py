from __future__ import annotations

from app.models import Article, StockQuote


class SampleMarketDataProvider:
    def fetch_quotes(self) -> list[StockQuote]:
        return [
            StockQuote("KOSPI", "005930", "삼성전자", 84200, 5.41, 1_3700_0000_0000),
            StockQuote("KOSPI", "000660", "SK하이닉스", 221000, 6.12, 1_9200_0000_0000),
            StockQuote("KOSPI", "005380", "현대차", 275000, 4.82, 1_1100_0000_0000),
            StockQuote("KOSDAQ", "196170", "알테오젠", 301500, 8.32, 1_2400_0000_0000),
            StockQuote("KOSDAQ", "086520", "에코프로", 91500, 5.91, 8600_0000_0000),
        ]


class SampleFinancialProvider:
    def operating_profits(self, ticker: str) -> list[int]:
        data = {
            "005930": [65670_0000_0000, 27980_0000_0000, 43380_0000_0000],
            "000660": [7680_0000_0000, 5120_0000_0000, -12410_0000_0000],
            "196170": [980_0000_0000, 520_0000_0000, 240_0000_0000],
            "086520": [610_0000_0000, -180_0000_0000, 720_0000_0000],
        }
        return data.get(ticker, [])


class SampleNewsProvider:
    def recent_articles(self, ticker: str, name: str) -> list[Article]:
        return [
            Article(f"{name}, 장중 강세 지속", "https://example.com/news/1", "Sample News", "2026-05-27"),
            Article(f"{name} 실적 전망 상향", "https://example.com/news/2", "Sample News", "2026-05-26"),
            Article(f"{name} 수급 개선 분석", "https://example.com/news/3", "Sample News", "2026-05-25"),
        ]
