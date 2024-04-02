from .db import get_db
from .config import API_KEY
import requests
from datetime import datetime


def hasSufficientBalance(userID, amount):
    # returns true if the user has balance greater than or equal to amount
    db = get_db()
    balance = db.execute(
        'SELECT cashBalance FROM users WHERE userID = ?',
        (userID,)
    ).fetchone()['cashBalance']

    if float(balance) >= float(amount):
        return True
    return False


def addToBalance(userID, amount):
    # adds amount to user's balance
    db = get_db()
    db.execute(
        'UPDATE users SET cashBalance = cashBalance + ? WHERE userID = ?',
        (amount, userID,)
    )
    db.commit()


def get_last_price(stock_symbol):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=' + stock_symbol + '&apikey=' + API_KEY
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get('Time Series (Daily)')
        if data is None:
            return None
        current_day = sorted(data.keys(), reverse=True)[0]
        return float(data.get(current_day).get("4. close"))
    return None


def add_transaction(userID, ticker, quantity, unitPrice, totalPrice, type):
    db = get_db()
    db.execute(
        'INSERT INTO transactions(userID, ticker, amount, unitPrice, totalPrice, orderType, dateTime)'
        'VALUES(?, ?, ?, ?, ?, ?, ?)',
        (userID, ticker, quantity, unitPrice, totalPrice, type, datetime.now())
    )
    db.commit()


def add_portfolio_object(userID, ticker, quantity):
    db = get_db()

    ticker_exists = ticker_in_portfolio(userID, ticker)

    if ticker_exists:
        db.execute(
            'UPDATE PortfolioObjects SET quantity = quantity + ? WHERE userID = ? and ticker = ?',
            (quantity, userID, ticker,)
        )
    else:
        db.execute(
            'INSERT INTO PortfolioObjects(userID, ticker, quantity)'
            'VALUES(?, ?, ?)',
            (userID, ticker, quantity)
        )

    db.commit()


def ticker_in_portfolio(userID, ticker):
    db = get_db()
    numRows = db.execute(
        'SELECT count(*) FROM PortfolioObjects WHERE userID = ? and ticker = ?',
        (userID, ticker,)
    ).fetchone()[0]

    if int(numRows) > 0:
        return True
    return False


def get_current_portfolio(userID):
    db = get_db()
    objects = db.execute(
        'SELECT * FROM PortfolioObjects WHERE userID = ?',
        (userID,)
    ).fetchall()

    return objects


def hasSufficientStock(userID, ticker, quantity):
    db = get_db()
    shares = db.execute(
        'SELECT * FROM PortfolioObjects WHERE userID = ? and ticker = ?',
        (userID, ticker)
    ).fetchone()['quantity']

    if int(shares) >= int(quantity):
        return True
    return False


def remove_portfolio_object(userID, ticker, quantity):
    db = get_db()

    db.execute(
        'UPDATE PortfolioObjects SET quantity = quantity - ? WHERE userID = ? and ticker = ?',
        (quantity, userID, ticker)
    )

    db.commit()

    db.execute(
        'DELETE FROM PortfolioObjects WHERE quantity = 0'
    )

    db.commit()