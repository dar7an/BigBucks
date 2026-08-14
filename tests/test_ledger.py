from __future__ import annotations

import pytest

from bigbucks.db import get_db
from bigbucks.ledger import (
    InvalidQuantity,
    InsufficientCash,
    InsufficientShares,
    cash_balance,
    execute_trade,
    holding_qty,
    transactions_for,
)
from bigbucks.market import get_last_price


def _user_id(app, username="bob"):
    with app.app_context():
        row = get_db().execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        return row["id"]


def test_qty_less_than_one_rejected(app, auth):
    auth.register()
    uid = _user_id(app)
    with app.app_context():
        cash_before = cash_balance(uid)
        with pytest.raises(InvalidQuantity):
            execute_trade(uid, "AAPL", 0, "buy")
        with pytest.raises(InvalidQuantity):
            execute_trade(uid, "AAPL", -3, "buy")
        assert cash_balance(uid) == cash_before
        assert holding_qty(uid, "AAPL") == 0


def test_buy_debits_cash_and_credits_shares(app, auth):
    auth.register()
    uid = _user_id(app)
    with app.app_context():
        px = get_last_price("AAPL")
        assert px is not None
        execute_trade(uid, "AAPL", 10, "buy")
        assert holding_qty(uid, "AAPL") == 10
        assert cash_balance(uid) == pytest.approx(1_000_000 - round(px * 10, 2))
        tx = transactions_for(uid)
        assert len(tx) == 1
        assert tx[0]["id"] is not None
        assert tx[0]["side"] == "buy"
        assert tx[0]["quantity"] == 10


def test_buy_insufficient_cash_is_atomic(app, auth):
    auth.register()
    uid = _user_id(app)
    with app.app_context():
        px = get_last_price("AAPL")
        too_many = int(1_000_000 / px) + 50
        with pytest.raises(InsufficientCash):
            execute_trade(uid, "AAPL", too_many, "buy")
        assert cash_balance(uid) == pytest.approx(1_000_000)
        assert holding_qty(uid, "AAPL") == 0
        assert transactions_for(uid) == []


def test_sell_credits_cash_keeps_history(app, auth):
    auth.register()
    uid = _user_id(app)
    with app.app_context():
        execute_trade(uid, "MSFT", 4, "buy")
        px = get_last_price("MSFT")
        cash_mid = cash_balance(uid)
        execute_trade(uid, "MSFT", 4, "sell")
        assert holding_qty(uid, "MSFT") == 0
        assert cash_balance(uid) == pytest.approx(cash_mid + round(px * 4, 2))
        rows = get_db().execute(
            "SELECT COUNT(*) AS n FROM historic_prices WHERE ticker = 'MSFT'"
        ).fetchone()
        assert rows["n"] > 100
        assert len(transactions_for(uid)) == 2


def test_sell_without_shares_fails(app, auth):
    auth.register()
    uid = _user_id(app)
    with app.app_context():
        with pytest.raises(InsufficientShares):
            execute_trade(uid, "NVDA", 1, "sell")
        assert cash_balance(uid) == pytest.approx(1_000_000)


def test_trade_form_rejects_qty_below_one(client, auth):
    auth.register()
    auth.login(username="bob", password="bobsmith1")
    res = client.post(
        "/trade",
        data={"ticker": "AAPL", "numShares": "0", "buyOrSell": "buy"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"whole number" in res.data or b"at least 1" in res.data
    with client.application.app_context():
        uid = _user_id(client.application, "bob")
        assert cash_balance(uid) == pytest.approx(1_000_000)
