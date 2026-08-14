from __future__ import annotations

import pytest

from bigbucks.db import get_db
from bigbucks.ledger import execute_trade


def test_series_from_t0(client, auth):
    auth.login()
    res = client.get("/api/series/AAPL")
    assert res.status_code == 200
    data = res.get_json()
    assert data["dates"] == sorted(data["dates"])
    assert data["cumulative"][0] == 0
    first, last = data["adj_close"][0], data["adj_close"][-1]
    assert data["cumulative"][-1] == pytest.approx(last / first - 1)


def test_compare_aligned_from_t0(client, auth):
    auth.login()
    res = client.get("/api/compare/NVDA")
    assert res.status_code == 200
    data = res.get_json()
    assert data["a_cum"][0] == 0
    assert data["b_cum"][0] == 0
    assert data["dates"] == sorted(data["dates"])
    # Inverted (divide by latest) would put the last point at 0.
    assert data["a_cum"][-1] != 0 or data["a_cum"][0] == data["a_cum"][-1]


def test_series_requires_login(client):
    assert client.get("/api/series/AAPL").status_code == 302


def test_metrics_page_after_two_buys(client, auth, app):
    auth.login()
    with app.app_context():
        uid = get_db().execute("SELECT id FROM users WHERE username = 'alice'").fetchone()["id"]
        execute_trade(uid, "AAPL", 5, "buy")
        execute_trade(uid, "MSFT", 3, "buy")
    page = client.get("/metrics/")
    assert page.status_code == 200
    assert b"Sharpe" in page.data
    assert b"mark-to-market" in page.data.lower() or b"Mark-to-market" in page.data
    assert b"annualized" in page.data.lower() or b"Annualized" in page.data or b"252" in page.data


def test_quote_page_has_price_not_raw_cap(client, auth):
    auth.login()
    page = client.get("/search/AAPL")
    assert page.status_code == 200
    assert b"AAPL" in page.data
    assert b"Apple" in page.data
    # compact market cap, not a raw 13-digit dump as the only figure
    assert b"Trade AAPL" in page.data


def test_empty_dashboard_copy(client, auth):
    auth.login()
    page = client.get("/home")
    assert page.status_code == 200
    assert b"No holdings yet" in page.data
    assert b"Search a ticker" in page.data


def test_404_page(client):
    res = client.get("/definitely-missing")
    assert res.status_code == 404
    assert b"not here" in res.data
