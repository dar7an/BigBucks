"""Atomic paper-trading ledger. One SQLite transaction per fill."""

from __future__ import annotations

from .db import get_db
from .market import get_company_name, get_last_price, last_bar, previous_bar


class LedgerError(Exception):
    """User-facing trade failure."""


class InsufficientCash(LedgerError):
    pass


class InsufficientShares(LedgerError):
    pass


class UnknownTicker(LedgerError):
    pass


class InvalidQuantity(LedgerError):
    pass


def get_user(user_id: int):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def cash_balance(user_id: int) -> float:
    row = get_db().execute(
        "SELECT cash_balance FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return float(row["cash_balance"]) if row else 0.0


def holdings(user_id: int) -> list[dict]:
    rows = get_db().execute(
        """SELECT ticker, quantity FROM holdings
           WHERE user_id = ? AND quantity > 0
           ORDER BY ticker""",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def holding_qty(user_id: int, ticker: str) -> int:
    row = get_db().execute(
        "SELECT quantity FROM holdings WHERE user_id = ? AND ticker = ?",
        (user_id, ticker.upper()),
    ).fetchone()
    return int(row["quantity"]) if row else 0


def average_cost(user_id: int, ticker: str) -> float | None:
    """Running average cost of remaining shares (buys add, sells keep the average)."""
    rows = get_db().execute(
        """SELECT side, quantity, unit_price FROM transactions
           WHERE user_id = ? AND ticker = ?
           ORDER BY id ASC""",
        (user_id, ticker.upper()),
    ).fetchall()
    qty = 0
    cost = 0.0
    for row in rows:
        q = int(row["quantity"])
        px = float(row["unit_price"])
        if row["side"] == "buy":
            cost += q * px
            qty += q
        else:
            if qty <= 0:
                continue
            avg = cost / qty
            sell = min(q, qty)
            cost -= avg * sell
            qty -= sell
    if qty <= 0:
        return None
    return cost / qty


def transactions_for(user_id: int) -> list[dict]:
    rows = get_db().execute(
        """SELECT id, ticker, quantity, unit_price, total_price, side, created_at
           FROM transactions
           WHERE user_id = ?
           ORDER BY id DESC""",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def execute_trade(user_id: int, ticker: str, quantity: int, side: str) -> dict:
    """Buy or sell whole shares at last adj close. All-or-nothing."""
    ticker = ticker.upper().strip()
    side = side.lower().strip()
    if side not in {"buy", "sell"}:
        raise LedgerError("Choose buy or sell.")
    if not isinstance(quantity, int) or quantity < 1:
        raise InvalidQuantity("Share quantity must be a whole number of at least 1.")
    price = get_last_price(ticker)
    if price is None:
        raise UnknownTicker(f"No last price for {ticker}.")
    total = round(price * quantity, 2)
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        if side == "buy":
            cur = db.execute(
                """UPDATE users
                   SET cash_balance = cash_balance - ?
                   WHERE id = ? AND cash_balance >= ?""",
                (total, user_id, total),
            )
            if cur.rowcount != 1:
                db.execute("ROLLBACK")
                raise InsufficientCash(
                    f"Not enough cash to buy {quantity} shares of {ticker} at ${price:,.2f}."
                )
            existing = holding_qty(user_id, ticker)
            if existing:
                db.execute(
                    """UPDATE holdings SET quantity = quantity + ?
                       WHERE user_id = ? AND ticker = ?""",
                    (quantity, user_id, ticker),
                )
            else:
                db.execute(
                    "INSERT INTO holdings (user_id, ticker, quantity) VALUES (?, ?, ?)",
                    (user_id, ticker, quantity),
                )
        else:
            owned = holding_qty(user_id, ticker)
            if owned < quantity:
                db.execute("ROLLBACK")
                raise InsufficientShares(
                    f"Not enough {ticker} shares to sell {quantity}."
                )
            if owned == quantity:
                db.execute(
                    "DELETE FROM holdings WHERE user_id = ? AND ticker = ?",
                    (user_id, ticker),
                )
            else:
                db.execute(
                    """UPDATE holdings SET quantity = quantity - ?
                       WHERE user_id = ? AND ticker = ? AND quantity >= ?""",
                    (quantity, user_id, ticker, quantity),
                )
            db.execute(
                "UPDATE users SET cash_balance = cash_balance + ? WHERE id = ?",
                (total, user_id),
            )
        db.execute(
            """INSERT INTO transactions
               (user_id, ticker, quantity, unit_price, total_price, side)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, ticker, quantity, price, total, side),
        )
        db.execute("COMMIT")
    except (InsufficientCash, InsufficientShares, InvalidQuantity, UnknownTicker, LedgerError):
        raise
    except Exception:
        db.execute("ROLLBACK")
        raise
    return {
        "ticker": ticker,
        "quantity": quantity,
        "side": side,
        "unit_price": price,
        "total_price": total,
    }


def marked_positions(user_id: int) -> list[dict]:
    positions = []
    for row in holdings(user_id):
        ticker = row["ticker"]
        qty = int(row["quantity"])
        last = last_bar(ticker)
        prev = previous_bar(ticker)
        last_px = float(last["adj_close_price"]) if last else None
        prev_px = float(prev["adj_close_price"]) if prev else last_px
        market_value = round(last_px * qty, 2) if last_px is not None else 0.0
        avg = average_cost(user_id, ticker)
        cost = round(avg * qty, 2) if avg is not None else None
        unrealized = round(market_value - cost, 2) if cost is not None else None
        day_pnl = round((last_px - prev_px) * qty, 2) if last_px is not None and prev_px is not None else 0.0
        positions.append(
            {
                "ticker": ticker,
                "name": get_company_name(ticker),
                "quantity": qty,
                "last": last_px,
                "previous": prev_px,
                "market_value": market_value,
                "avg_cost": avg,
                "cost": cost,
                "unrealized": unrealized,
                "day_pnl": day_pnl,
                "as_of": last["closing_date"] if last else None,
            }
        )
    return positions


def account_snapshot(user_id: int, starting_cash: float) -> dict:
    cash = cash_balance(user_id)
    positions = marked_positions(user_id)
    invested = sum(p["market_value"] for p in positions)
    equity = cash + invested
    total_pnl = equity - starting_cash
    day_pnl = sum(p["day_pnl"] for p in positions)
    return {
        "cash": cash,
        "invested": invested,
        "equity": equity,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl / starting_cash if starting_cash else 0.0,
        "day_pnl": day_pnl,
        "positions": positions,
        "starting_cash": starting_cash,
    }


def system_holdings() -> list[dict]:
    """Aggregate shares across users. Does not join the journal."""
    db = get_db()
    rows = db.execute(
        """SELECT ticker, SUM(quantity) AS shares
           FROM holdings
           GROUP BY ticker
           ORDER BY ticker"""
    ).fetchall()
    out = []
    for row in rows:
        ticker = row["ticker"]
        last = get_last_price(ticker)
        out.append(
            {
                "ticker": ticker,
                "name": get_company_name(ticker),
                "shares": int(row["shares"]),
                "last": last,
                "market_value": round((last or 0) * int(row["shares"]), 2),
            }
        )
    return out


def tape_for_day(day_iso: str) -> list[dict]:
    rows = get_db().execute(
        """SELECT ticker,
                  SUM(CASE WHEN side = 'buy' THEN quantity ELSE 0 END) AS shares_bought,
                  SUM(CASE WHEN side = 'sell' THEN quantity ELSE 0 END) AS shares_sold
           FROM transactions
           WHERE date(created_at) = ?
           GROUP BY ticker
           ORDER BY ticker""",
        (day_iso,),
    ).fetchall()
    return [
        {
            "ticker": r["ticker"],
            "name": get_company_name(r["ticker"]),
            "shares_bought": int(r["shares_bought"] or 0),
            "shares_sold": int(r["shares_sold"] or 0),
        }
        for r in rows
    ]


def list_users() -> list[dict]:
    rows = get_db().execute(
        """SELECT id, username, first_name, last_name, email, cash_balance, role, created_at
           FROM users
           ORDER BY username"""
    ).fetchall()
    return [dict(r) for r in rows]


def unique_held_tickers() -> list[str]:
    rows = get_db().execute(
        "SELECT DISTINCT ticker FROM holdings ORDER BY ticker"
    ).fetchall()
    return [r["ticker"] for r in rows]


def tickers_of(user_id: int) -> list[str]:
    return [h["ticker"] for h in holdings(user_id)]
