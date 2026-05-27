from __future__ import annotations

KIND_IPO_SCHEDULE_URL = "https://kind.krx.co.kr/listinvstg/pubofrprogcom.do?method=searchPubofrProgComMain"


def official_ipo_url(company_name: str) -> str:
    return KIND_IPO_SCHEDULE_URL
