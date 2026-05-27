from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from app.models import Article
from app.utils import clean_html, http_json


KST = timezone(timedelta(hours=9))


class NaverNewsProvider:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def recent_articles(self, ticker: str, name: str) -> list[Article]:
        query = f'"{name}" {ticker} 주가 실적 투자'
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        params = {"query": query, "display": "20", "sort": "sim"}
        data = http_json("https://openapi.naver.com/v1/search/news.json", params=params, headers=headers)
        threshold = datetime.now(tz=KST) - timedelta(days=7)
        seen: set[str] = set()
        articles: list[Article] = []
        for item in data.get("items", []):
            published = _parse_pub_date(item.get("pubDate"))
            if published is None or published < threshold:
                continue
            link = item.get("originallink") or item.get("link") or ""
            if not link or link in seen:
                continue
            seen.add(link)
            articles.append(
                Article(
                    title=clean_html(item.get("title", "")),
                    link=link,
                    source=_source_from_link(link),
                    published_at=published.date().isoformat(),
                )
            )
            if len(articles) == 3:
                break
        return articles


def _parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(KST)
    except (TypeError, ValueError):
        return None


def _source_from_link(link: str) -> str:
    host = urlparse(link).netloc
    return host.removeprefix("www.") or "news"

