from __future__ import annotations

import io
import urllib.parse
import urllib.request
import zipfile
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from app.utils import http_json, read_json, write_json


class DartFinancialProvider:
    def __init__(self, api_key: str, cache_path: Path):
        self.api_key = api_key
        self.cache_path = cache_path

    def operating_profits(self, ticker: str) -> list[int]:
        corp_code = self._corp_code_for_ticker(ticker)
        if not corp_code:
            return []
        profits: list[int] = []
        for year in range(date.today().year - 1, date.today().year - 6, -1):
            value = self._annual_operating_profit(corp_code, str(year), "CFS")
            if value is None:
                value = self._annual_operating_profit(corp_code, str(year), "OFS")
            if value is not None:
                profits.append(value)
            if len(profits) == 3:
                break
        return profits

    def _corp_code_for_ticker(self, ticker: str) -> str | None:
        data = read_json(self.cache_path, default=None)
        if data is None:
            data = self._download_corp_codes()
            write_json(self.cache_path, data)
        row = data.get(ticker)
        return row.get("corp_code") if row else None

    def _download_corp_codes(self) -> dict[str, dict[str, str]]:
        url = "https://opendart.fss.or.kr/api/corpCode.xml"
        params = urllib.parse.urlencode({"crtfc_key": self.api_key})
        with urllib.request.urlopen(f"{url}?{params}", timeout=30) as response:
            zip_bytes = response.read()
        if not zip_bytes.startswith(b"PK"):
            text = zip_bytes.decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenDART corpCode did not return a zip file: {text[:500]}")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            xml_bytes = archive.read("CORPCODE.xml")
        root = ElementTree.fromstring(xml_bytes)
        result: dict[str, dict[str, str]] = {}
        for item in root.findall("list"):
            stock_code = (item.findtext("stock_code") or "").strip()
            if not stock_code:
                continue
            result[stock_code] = {
                "corp_code": (item.findtext("corp_code") or "").strip(),
                "corp_name": (item.findtext("corp_name") or "").strip(),
            }
        return result

    def _annual_operating_profit(self, corp_code: str, year: str, fs_div: str) -> int | None:
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": year,
            "reprt_code": "11011",
            "fs_div": fs_div,
        }
        data = http_json("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json", params=params)
        if data.get("status") != "000":
            return None
        for row in data.get("list", []):
            if _is_operating_profit_row(row):
                return _money_to_int(row.get("thstrm_amount"))
        return None


def _is_operating_profit_row(row: dict[str, Any]) -> bool:
    account_id = str(row.get("account_id") or "")
    account_nm = str(row.get("account_nm") or "")
    if "OperatingIncomeLoss" in account_id or "ProfitLossFromOperatingActivities" in account_id:
        return True
    return account_nm in {"영업이익", "영업손실"}


def _money_to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    text = str(value).replace(",", "").strip()
    try:
        return int(text)
    except ValueError:
        return None
