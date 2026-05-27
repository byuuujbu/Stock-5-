from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any

from app.models import IpoItem
from app.providers.kind_disclosure import official_ipo_url
from app.utils import http_text


IPO_KOREA_URL = "https://ipokorea.kr/"


class IpoKoreaProvider:
    def fetch_monthly_ipos(self, today: date | None = None) -> list[IpoItem]:
        target = today or date.today()
        payload = self._fetch_payload()
        rows = payload.get("initialAllIPOs", [])
        items = [_to_ipo_item(row) for row in rows]
        return sorted(
            [
                item
                for item in items
                if _same_month(item.subscription_start, target) or _same_month(item.listing_date, target)
            ],
            key=lambda item: (item.subscription_start or "9999-99-99", item.company_name),
        )

    def _fetch_payload(self) -> dict[str, Any]:
        html = http_text(IPO_KOREA_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        chunks = []
        for match in re.finditer(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html):
            chunks.append(json.loads(f'"{match.group(1)}"'))
        flight = "".join(chunks)
        line = next((item for item in flight.splitlines() if item.startswith("7:")), None)
        if not line:
            raise RuntimeError("IPO Korea payload not found.")
        component = json.loads(line[2:])
        return component[3]


def _to_ipo_item(row: dict[str, Any]) -> IpoItem:
    managers = row.get("대표주관사") or row.get("주관사_정규화") or ""
    if isinstance(managers, list):
        managers = ", ".join(str(item) for item in managers)
    return IpoItem(
        company_name=str(row.get("회사명") or ""),
        market=str(row.get("시장구분") or ""),
        status=str(row.get("status") or ""),
        subscription_start=_date_text(row.get("청약시작일")),
        subscription_end=_date_text(row.get("청약종료일")),
        listing_date=_date_text(row.get("상장일")),
        price_min=_int_or_none(row.get("희망공모가_하단")),
        price_max=_int_or_none(row.get("희망공모가_상단")),
        final_price=_int_or_none(row.get("확정공모가")),
        lead_managers=str(managers),
        source_url=IPO_KOREA_URL,
        official_url=official_ipo_url(str(row.get("회사명") or "")),
    )


def _same_month(value: str, target: date) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return False
    return parsed.year == target.year and parsed.month == target.month


def _date_text(value: Any) -> str:
    return str(value or "")


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(float(str(value).replace(",", "")))
