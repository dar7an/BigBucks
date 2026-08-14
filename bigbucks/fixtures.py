"""Deterministic fixture prices, symbol metadata, and demo accounts.

The app and tests run without Alpha Vantage. Series are a one-factor model
with a fixed numpy seed so Sharpe/corr stay stable across clones.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
from werkzeug.security import generate_password_hash

TRADING_DAYS = 504  # ~ two years of sessions

# One-factor parameters: start price, annualized drift, beta, idiosyncratic vol.
UNIVERSE = {
    "SPY": {"start": 450.0, "mu": 0.09, "beta": 1.00, "idio": 0.002, "name": "SPDR S&P 500 ETF Trust", "sector": "ETF", "industry": "Large Blend", "exchange": "NYSE Arca"},
    "AAPL": {"start": 175.0, "mu": 0.14, "beta": 1.15, "idio": 0.012, "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics", "exchange": "NASDAQ"},
    "MSFT": {"start": 380.0, "mu": 0.13, "beta": 1.05, "idio": 0.010, "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software", "exchange": "NASDAQ"},
    "NVDA": {"start": 95.0, "mu": 0.22, "beta": 1.65, "idio": 0.018, "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors", "exchange": "NASDAQ"},
    "GOOGL": {"start": 140.0, "mu": 0.12, "beta": 1.10, "idio": 0.011, "name": "Alphabet Inc. Class A", "sector": "Communication Services", "industry": "Internet Content", "exchange": "NASDAQ"},
    "AMZN": {"start": 170.0, "mu": 0.13, "beta": 1.20, "idio": 0.013, "name": "Amazon.com, Inc.", "sector": "Consumer Cyclical", "industry": "Internet Retail", "exchange": "NASDAQ"},
    "META": {"start": 470.0, "mu": 0.15, "beta": 1.30, "idio": 0.014, "name": "Meta Platforms, Inc.", "sector": "Communication Services", "industry": "Internet Content", "exchange": "NASDAQ"},
}

NEWS = {
    "AAPL": [
        ("Apple reports record services revenue", "Services grew faster than hardware in the latest quarter, with installed-base engagement cited as the driver."),
        ("iPhone demand steadies in China", "Channel checks pointed to a flatter Greater China sell-through versus the prior year."),
    ],
    "MSFT": [
        ("Azure growth remains the story", "Cloud billings beat consensus; management guided to continued capacity investment."),
        ("Office 365 seats keep compounding", "Commercial seat additions offset a slower PC-OEM cycle."),
    ],
    "NVDA": [
        ("Data-center GPUs stay sold out", "Management said lead times remain extended for flagship accelerators."),
        ("Inference mix starts to matter", "Software and networking attached to training clusters showed up in commentary."),
    ],
    "GOOGL": [
        ("Search stays the cash engine", "Advertising held up even as YouTube and cloud took more of the narrative."),
        ("Cloud backlog grows", "Google Cloud's remaining performance obligation rose on multi-year deals."),
    ],
    "AMZN": [
        ("AWS margins recover a step", "Operating income in the cloud segment improved on mix and cost control."),
        ("Retail ads outgrow 1P sales", "Advertising remains the fastest profitable line in North America stores."),
    ],
    "META": [
        ("Reels ads close more of the gap", "Family-of-apps pricing improved as short-form inventory matured."),
        ("Reality Labs still a drag", "The hardware bet remains a multi-year cost center against apps cash flow."),
    ],
    "SPY": [
        ("S&P 500 holds near highs", "Breadth improved as equal-weight lagged less than the prior month."),
        ("Rate-cut odds swing the tape", "Index returns clustered around CPI and FOMC prints."),
    ],
}


def weekdays_ending(n: int, end: date | None = None) -> list[date]:
    """Return n weekdays, oldest first, ending on `end` (or a fixed teaching date)."""
    day = end or date(2026, 8, 13)
    out: list[date] = []
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day)
        day -= timedelta(days=1)
    out.reverse()
    return out


def generate_bars(seed: int = 18) -> dict[str, list[dict]]:
    """Build OHLCV bars for every ticker in UNIVERSE."""
    rng = np.random.default_rng(seed)
    days = weekdays_ending(TRADING_DAYS)
    n = len(days)
    market = rng.normal(0.00035, 0.009, size=n)
    out: dict[str, list[dict]] = {}
    for ticker, spec in UNIVERSE.items():
        daily_mu = spec["mu"] / 252
        rets = daily_mu + spec["beta"] * market + rng.normal(0.0, spec["idio"], size=n)
        prices = np.empty(n)
        prices[0] = spec["start"]
        for i in range(1, n):
            prices[i] = prices[i - 1] * (1.0 + rets[i])
        rows = []
        for i, dt in enumerate(days):
            px = float(prices[i])
            prev = float(prices[i - 1]) if i else px
            high = max(prev, px) * (1.0 + abs(float(rng.normal(0, 0.004))))
            low = min(prev, px) * (1.0 - abs(float(rng.normal(0, 0.004))))
            open_px = prev * (1.0 + float(rng.normal(0, 0.002)))
            volume = int(rng.integers(12_000_000, 90_000_000))
            rows.append(
                {
                    "ticker": ticker,
                    "closing_date": dt.isoformat(),
                    "open_price": round(open_px, 4),
                    "high_price": round(high, 4),
                    "low_price": round(low, 4),
                    "close_price": round(px, 4),
                    "adj_close_price": round(px, 4),
                    "volume": volume,
                }
            )
        out[ticker] = rows
    return out


def overview_for(ticker: str, last_price: float) -> dict:
    spec = UNIVERSE[ticker]
    shares = {
        "AAPL": 15_300_000_000,
        "MSFT": 7_430_000_000,
        "NVDA": 24_500_000_000,
        "GOOGL": 12_300_000_000,
        "AMZN": 10_400_000_000,
        "META": 2_530_000_000,
        "SPY": 900_000_000,
    }[ticker]
    mcap = last_price * shares
    pe = {"AAPL": 32.4, "MSFT": 35.1, "NVDA": 48.6, "GOOGL": 24.8, "AMZN": 38.2, "META": 26.5, "SPY": None}[ticker]
    eps = None if pe is None else round(last_price / pe, 2)
    div_yield = {"AAPL": 0.0044, "MSFT": 0.0072, "NVDA": 0.0003, "GOOGL": 0.0031, "AMZN": 0.0, "META": 0.0038, "SPY": 0.0128}[ticker]
    return {
        "Symbol": ticker,
        "Name": spec["name"],
        "Sector": spec["sector"],
        "Industry": spec["industry"],
        "Exchange": spec["exchange"],
        "MarketCapitalization": int(mcap),
        "PERatio": pe,
        "EPS": eps,
        "DividendPerShare": round(last_price * div_yield, 2) if div_yield else 0.0,
        "DividendYield": div_yield,
        "52WeekHigh": None,
        "52WeekLow": None,
    }


def seed_market(db) -> None:
    bars = generate_bars()
    price_rows = []
    symbol_rows = []
    for ticker, rows in bars.items():
        for row in rows:
            price_rows.append(
                (
                    row["ticker"],
                    row["closing_date"],
                    row["open_price"],
                    row["high_price"],
                    row["low_price"],
                    row["close_price"],
                    row["adj_close_price"],
                    row["volume"],
                )
            )
        last = rows[-1]["adj_close_price"]
        year = rows[-252:] if len(rows) >= 252 else rows
        highs = max(r["high_price"] for r in year)
        lows = min(r["low_price"] for r in year)
        overview = overview_for(ticker, last)
        overview["52WeekHigh"] = round(highs, 2)
        overview["52WeekLow"] = round(lows, 2)
        spec = UNIVERSE[ticker]
        symbol_rows.append(
            (
                ticker,
                spec["name"],
                spec["sector"],
                spec["industry"],
                spec["exchange"],
                json.dumps(overview),
            )
        )
    db.executemany(
        """INSERT INTO historic_prices
           (ticker, closing_date, open_price, high_price, low_price, close_price, adj_close_price, volume)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        price_rows,
    )
    db.executemany(
        """INSERT INTO symbols (ticker, name, sector, industry, exchange, overview_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        symbol_rows,
    )
    db.commit()


def seed_demo_users(db) -> None:
    """Teaching accounts. Documented in the README; change the password in anything shared."""
    rows = [
        ("alice", "Alice", "Ng", "alice@example.com", "alicepass", "user"),
        ("admin", "Ada", "Min", "admin@example.com", "adminpass", "admin"),
    ]
    for username, first, last, email, password, role in rows:
        db.execute(
            """INSERT OR IGNORE INTO users
               (username, first_name, last_name, email, password_hash, cash_balance, role)
               VALUES (?, ?, ?, ?, ?, 1000000, ?)""",
            (username, first, last, email, generate_password_hash(password), role),
        )
    db.commit()


def news_for(ticker: str) -> list[dict]:
    items = NEWS.get(ticker.upper(), NEWS["SPY"])
    return [{"title": title, "summary": summary, "url": "#"} for title, summary in items]
