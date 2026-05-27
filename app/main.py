from __future__ import annotations

import secrets

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException

from app.config import get_settings
from app.db import list_runs, load_ipos, load_run
from app.utils import money_krw


app = FastAPI(title="Domestic Stock Selection Agent")
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["money_krw"] = money_krw
security = HTTPBasic(auto_error=False)


def require_auth(credentials: HTTPBasicCredentials | None = Depends(security)) -> None:
    settings = get_settings()
    if not settings.web_auth_username and not settings.web_auth_password:
        return
    if credentials is None:
        _raise_auth()
    username_ok = secrets.compare_digest(credentials.username, settings.web_auth_username)
    password_ok = secrets.compare_digest(credentials.password, settings.web_auth_password)
    if not (username_ok and password_ok):
        _raise_auth()


def _raise_auth() -> None:
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )


@app.get("/")
def dashboard(request: Request, _: None = Depends(require_auth)):
    settings = get_settings()
    run_date, stocks = load_run(settings.db_path)
    _, ipos = load_ipos(settings.db_path, run_date)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "run_date": run_date,
            "stocks": stocks,
            "stock_groups": _group_by_profit_tier(stocks),
            "ipos": ipos,
            "active": "dashboard",
        },
    )


@app.get("/history")
def history(request: Request, _: None = Depends(require_auth)):
    settings = get_settings()
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "runs": list_runs(settings.db_path),
            "active": "history",
        },
    )


@app.get("/history/{run_date}")
def history_detail(request: Request, run_date: str, _: None = Depends(require_auth)):
    settings = get_settings()
    actual_date, stocks = load_run(settings.db_path, run_date)
    _, ipos = load_ipos(settings.db_path, actual_date)
    if actual_date is None:
        return RedirectResponse(url="/history")
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "run_date": actual_date,
            "stocks": stocks,
            "stock_groups": _group_by_profit_tier(stocks),
            "ipos": ipos,
            "active": "history",
        },
    )


def _group_by_profit_tier(stocks: list[dict]) -> list[dict]:
    labels = {
        "3Y": "최근 3년 연간 영업이익 흑자",
        "2Y": "최근 2년 연간 영업이익 흑자",
        "1Y": "최근 1년 연간 영업이익 흑자",
    }
    groups = []
    for tier in ("3Y", "2Y", "1Y"):
        items = [stock for stock in stocks if stock.get("profit_tier", "3Y") == tier]
        groups.append({"tier": tier, "label": labels[tier], "stocks": items})
    return groups
