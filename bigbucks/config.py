"""Environment-based settings. No secrets belong in this file."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _bool(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    MARKET_DATA_SOURCE = os.environ.get("MARKET_DATA_SOURCE", "fixture").strip().lower()
    RISK_FREE_RATE = float(os.environ.get("RISK_FREE_RATE", "0.043"))
    STARTING_CASH = float(os.environ.get("STARTING_CASH", "1000000"))
    SEED_DEMO_USERS = _bool("SEED_DEMO_USERS", "1")
    TRADING_DAYS_PER_YEAR = 252
    METRICS_LOOKBACK_DAYS = 365
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 8 * 60 * 60
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", "0")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    JSON_SORT_KEYS = False
