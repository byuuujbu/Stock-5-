from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.db import save_run
from app.notifiers.telegram import TelegramNotifier
from app.providers.dart import DartFinancialProvider
from app.providers.ipo_korea import IpoKoreaProvider
from app.providers.kis import KisMarketDataProvider
from app.providers.naver_news import NaverNewsProvider
from app.providers.sample import SampleFinancialProvider, SampleMarketDataProvider, SampleNewsProvider
from app.screener import Screener


KST = timezone(timedelta(hours=9))


def build_screener(sample: bool):
    settings = get_settings()
    if sample:
        return Screener(SampleMarketDataProvider(), SampleFinancialProvider(), SampleNewsProvider())
    return Screener(
        KisMarketDataProvider(
            settings.kis_base_url,
            settings.kis_app_key,
            settings.kis_app_secret,
            settings.kis_universe_csv,
            min_interval_seconds=settings.kis_min_interval_seconds,
            token_cache_path=settings.kis_token_cache,
        ),
        DartFinancialProvider(settings.dart_api_key, settings.dart_corp_code_cache),
        NaverNewsProvider(settings.naver_client_id, settings.naver_client_secret),
    )


def run_daily(sample: bool | None = None, notify: bool = True) -> int:
    settings = get_settings()
    use_sample = settings.sample_mode if sample is None else sample
    if not use_sample and not settings.has_real_api_config:
        missing = "KIS_APP_KEY/KIS_APP_SECRET/DART_API_KEY/NAVER_CLIENT_ID/NAVER_CLIENT_SECRET"
        raise RuntimeError(f"Real API mode requires .env values: {missing}")
    run_date = datetime.now(tz=KST).date().isoformat()
    screener = build_screener(use_sample)
    stocks = screener.run()
    ipos = [] if use_sample else IpoKoreaProvider().fetch_monthly_ipos()
    save_run(settings.db_path, run_date, "sample" if use_sample else "real", stocks, ipos)
    if notify:
        TelegramNotifier(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
            settings.base_url,
        ).send_daily_result(run_date, stocks, ipos)
    print(f"saved {len(stocks)} selections and {len(ipos)} IPOs for {run_date}")
    return len(stocks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Run with deterministic sample data")
    parser.add_argument("--no-notify", action="store_true", help="Do not send Telegram notification")
    args = parser.parse_args()
    run_daily(sample=args.sample, notify=not args.no_notify)


if __name__ == "__main__":
    main()
