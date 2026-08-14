"""Market data: HistoricPriceData first, Alpha Vantage optional.

Live calls use the free TIME_SERIES_DAILY endpoint (not the premium
TIME_SERIES_DAILY_ADJUSTED). Adjusted close is stored as close on the free
series. Errors, notes, and rate-limit JSON never raise KeyError.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

import requests
from flask import current_app

from .db import get_db
from . import fixtures

AV_URL = "https://www.alphavantage.co/query"


class MarketDataError(Exception):
    """User-facing market-data failure."""


class RateLimitError(MarketDataError):
    pass


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def known_tickers() -> list[str]:
    db = get_db()
    rows = db.execute("SELECT ticker FROM symbols ORDER BY ticker").fetchall()
    return [r["ticker"] for r in rows]


def get_symbol(ticker: str) -> dict | None:
    row = get_db().execute(
        "SELECT * FROM symbols WHERE ticker = ?", (ticker.upper(),)
    ).fetchone()
    return dict(row) if row else None


def get_company_name(ticker: str) -> str:
    row = get_symbol(ticker)
    return row["name"] if row else ticker.upper()


def last_bar(ticker: str) -> dict | None:
    row = get_db().execute(
        """SELECT * FROM historic_prices
           WHERE ticker = ?
           ORDER BY closing_date DESC
           LIMIT 1""",
        (ticker.upper(),),
    ).fetchone()
    return dict(row) if row else None


def previous_bar(ticker: str) -> dict | None:
    row = get_db().execute(
        """SELECT * FROM historic_prices
           WHERE ticker = ?
           ORDER BY closing_date DESC
           LIMIT 1 OFFSET 1""",
        (ticker.upper(),),
    ).fetchone()
    return dict(row) if row else None


def get_last_price(ticker: str) -> float | None:
    bar = last_bar(ticker)
    return float(bar["adj_close_price"]) if bar else None


def price_series(ticker: str) -> list[dict]:
    rows = get_db().execute(
        """SELECT closing_date, adj_close_price, close_price, volume
           FROM historic_prices
           WHERE ticker = ?
           ORDER BY closing_date ASC""",
        (ticker.upper(),),
    ).fetchall()
    return [dict(r) for r in rows]


def source() -> str:
    return (current_app.config.get("MARKET_DATA_SOURCE") or "fixture").lower()


def ensure_history(ticker: str) -> None:
    """Load history if missing. Never called as a login side-effect."""
    ticker = ticker.upper()
    if last_bar(ticker):
        return
    if source() == "alphavantage":
        refresh_from_alphavantage(ticker)
        return
    if ticker in fixtures.UNIVERSE:
        # Fixture universe is seeded on init-db; a miss means the DB was not seeded.
        raise MarketDataError(
            f"No price history for {ticker}. Run flask --app bigbucks init-db."
        )
    raise MarketDataError(
        f"{ticker} is not in the fixture universe. Seeded tickers: {', '.join(sorted(fixtures.UNIVERSE))}."
    )


def _parse_av_daily(payload: dict) -> list[dict]:
    if payload.get("Note") or payload.get("Information"):
        raise RateLimitError(
            "Alpha Vantage rate-limited this key. Quotes will keep using cached prices."
        )
    if payload.get("Error Message"):
        raise MarketDataError("Alpha Vantage does not recognize that ticker.")
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict):
        raise MarketDataError("Unexpected market-data response. Try again later.")
    rows = []
    cutoff = date.today() - timedelta(days=5 * 365)
    for day, values in series.items():
        dt = _as_date(day)
        if dt is None or dt < cutoff:
            continue
        close = float(values["4. close"])
        adj = float(values.get("5. adjusted close", close))
        rows.append(
            {
                "closing_date": dt.isoformat(),
                "open_price": float(values["1. open"]),
                "high_price": float(values["2. high"]),
                "low_price": float(values["3. low"]),
                "close_price": close,
                "adj_close_price": adj,
                "volume": int(float(values["5. volume"] if "5. volume" in values else values.get("6. volume", 0))),
            }
        )
    rows.sort(key=lambda r: r["closing_date"])
    return rows


def refresh_from_alphavantage(ticker: str) -> int:
    """Insert bars newer than what we already store. Returns inserted count."""
    ticker = ticker.upper()
    key = current_app.config.get("ALPHA_VANTAGE_API_KEY") or ""
    if not key:
        raise MarketDataError("ALPHA_VANTAGE_API_KEY is not set.")
    try:
        response = requests.get(
            AV_URL,
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "outputsize": "compact",
                "apikey": key,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise MarketDataError("Could not reach Alpha Vantage.") from exc
    except ValueError as exc:
        raise MarketDataError("Alpha Vantage returned a non-JSON body.") from exc

    rows = _parse_av_daily(payload)
    db = get_db()
    last = db.execute(
        "SELECT MAX(closing_date) FROM historic_prices WHERE ticker = ?", (ticker,)
    ).fetchone()[0]
    last_d = _as_date(last)
    new_rows = []
    for row in rows:
        if last_d and date.fromisoformat(row["closing_date"]) <= last_d:
            continue
        new_rows.append(
            (
                ticker,
                row["closing_date"],
                row["open_price"],
                row["high_price"],
                row["low_price"],
                row["close_price"],
                row["adj_close_price"],
                row["volume"],
            )
        )
    if new_rows:
        db.executemany(
            """INSERT OR IGNORE INTO historic_prices
               (ticker, closing_date, open_price, high_price, low_price, close_price, adj_close_price, volume)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            new_rows,
        )
        db.commit()
    if not last_bar(ticker):
        raise MarketDataError(f"No usable bars returned for {ticker}.")
    _upsert_symbol_name(ticker)
    return len(new_rows)


def _upsert_symbol_name(ticker: str) -> None:
    if get_symbol(ticker):
        return
    get_db().execute(
        """INSERT INTO symbols (ticker, name, sector, industry, exchange, overview_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ticker, ticker, None, None, None, json.dumps({"Symbol": ticker, "Name": ticker})),
    )
    get_db().commit()


def quote_bundle(ticker: str) -> dict:
    ticker = ticker.upper()
    ensure_history(ticker)
    last = last_bar(ticker)
    prev = previous_bar(ticker)
    symbol = get_symbol(ticker) or {}
    overview = {}
    if symbol.get("overview_json"):
        try:
            overview = json.loads(symbol["overview_json"])
        except json.JSONDecodeError:
            overview = {}
    last_px = float(last["adj_close_price"])
    prev_px = float(prev["adj_close_price"]) if prev else last_px
    change = last_px - prev_px
    change_pct = change / prev_px if prev_px else 0.0
    overview.setdefault("Symbol", ticker)
    overview.setdefault("Name", symbol.get("name") or ticker)
    overview.setdefault("Sector", symbol.get("sector") or "—")
    overview.setdefault("Industry", symbol.get("industry") or "—")
    overview.setdefault("Exchange", symbol.get("exchange") or "—")
    return {
        "ticker": ticker,
        "name": overview["Name"],
        "last": last_px,
        "previous": prev_px,
        "open": float(last["open_price"]),
        "high": float(last["high_price"]),
        "low": float(last["low_price"]),
        "volume": int(last["volume"]),
        "change": change,
        "change_pct": change_pct,
        "as_of": last["closing_date"],
        "overview": overview,
        "news": fixtures.news_for(ticker),
    }
