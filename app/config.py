from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    db_path: Path
    base_url: str
    sample_mode: bool
    web_auth_username: str
    web_auth_password: str
    kis_base_url: str
    kis_app_key: str
    kis_app_secret: str
    kis_universe_csv: Path
    kis_min_interval_seconds: float
    kis_token_cache: Path
    dart_api_key: str
    dart_corp_code_cache: Path
    naver_client_id: str
    naver_client_secret: str
    telegram_bot_token: str
    telegram_chat_id: str

    @property
    def has_real_api_config(self) -> bool:
        return all(
            [
                self.kis_app_key,
                self.kis_app_secret,
                self.dart_api_key,
                self.naver_client_id,
                self.naver_client_secret,
            ]
        )


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        db_path=Path(os.getenv("APP_DB_PATH", "data/stock_agent.sqlite3")),
        base_url=os.getenv("APP_BASE_URL", "http://127.0.0.1:8000"),
        sample_mode=_bool_env("APP_SAMPLE_MODE", False),
        web_auth_username=os.getenv("WEB_AUTH_USERNAME", ""),
        web_auth_password=os.getenv("WEB_AUTH_PASSWORD", ""),
        kis_base_url=os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"),
        kis_app_key=os.getenv("KIS_APP_KEY", ""),
        kis_app_secret=os.getenv("KIS_APP_SECRET", ""),
        kis_universe_csv=Path(os.getenv("KIS_UNIVERSE_CSV", "data/universe.csv")),
        kis_min_interval_seconds=float(os.getenv("KIS_MIN_INTERVAL_SECONDS", "0.12")),
        kis_token_cache=Path(os.getenv("KIS_TOKEN_CACHE", "data/kis_token.json")),
        dart_api_key=os.getenv("DART_API_KEY", ""),
        dart_corp_code_cache=Path(os.getenv("DART_CORP_CODE_CACHE", "data/dart_corp_codes.json")),
        naver_client_id=os.getenv("NAVER_CLIENT_ID", ""),
        naver_client_secret=os.getenv("NAVER_CLIENT_SECRET", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
