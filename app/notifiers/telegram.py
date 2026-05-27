from __future__ import annotations

from app.models import IpoItem, SelectedStock
from app.utils import http_json, money_krw


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, base_url: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_daily_result(self, run_date: str, stocks: list[SelectedStock], ipos: list[IpoItem] | None = None) -> None:
        if not self.enabled:
            return
        lines = [
            f"[{run_date} 국내 주식 선별 결과]",
            "조건: 거래대금 1조 이상 / 최근 3년 영업이익 흑자 / 당일 상승률 5% 이상",
            "",
        ]
        if not stocks:
            lines.append("선정 종목 없음")
        for tier, label in (
            ("3Y", "최근 3년 연간 영업이익 흑자"),
            ("2Y", "최근 2년 연간 영업이익 흑자"),
            ("1Y", "최근 1년 연간 영업이익 흑자"),
        ):
            tier_stocks = [stock for stock in stocks if (_field(stock, "profit_tier") or "3Y") == tier]
            lines.extend(["", f"[{label}]"])
            if not tier_stocks:
                lines.append("선정 종목 없음")
                continue
            for index, stock in enumerate(tier_stocks, start=1):
                name = _field(stock, "name")
                ticker = _field(stock, "ticker")
                change_rate = float(_field(stock, "change_rate") or 0)
                trading_value = int(_field(stock, "trading_value") or 0)
                lines.append(
                    f"{index}. {name} ({ticker}) "
                    f"{change_rate:.2f}%, 거래대금 {money_krw(trading_value)}"
                )
        if ipos:
            lines.extend(["", "[이번 달 IPO 일정]"])
            for index, ipo in enumerate(ipos[:10], start=1):
                schedule = _schedule_text(ipo)
                price = _price_text(ipo)
                lines.append(f"{index}. {_field(ipo, 'company_name')} {schedule} {price}".strip())
                source_url = _field(ipo, "source_url")
                if source_url:
                    lines.append(f"   IPO Korea: {source_url}")
        lines.extend(["", f"Dashboard: {self.base_url}"])
        http_json(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            method="POST",
            body={"chat_id": self.chat_id, "text": "\n".join(lines), "disable_web_page_preview": True},
        )


def _schedule_text(ipo: IpoItem) -> str:
    subscription_start = _field(ipo, "subscription_start")
    subscription_end = _field(ipo, "subscription_end")
    listing_date = _field(ipo, "listing_date")
    if subscription_start and subscription_end:
        return f"청약 {subscription_start}~{subscription_end}"
    if listing_date:
        return f"상장 {listing_date}"
    return ""


def _price_text(ipo: IpoItem) -> str:
    final_price = _field(ipo, "final_price")
    price_min = _field(ipo, "price_min")
    price_max = _field(ipo, "price_max")
    if final_price:
        return f"공모가 {int(final_price):,}원"
    if price_min and price_max:
        return f"희망 {int(price_min):,}~{int(price_max):,}원"
    return ""


def _field(item, name: str):
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name)
