from typing import Optional, List, Dict
from .db import get_db
from .config import API_KEY
import requests
from datetime import datetime


def has_sufficient_balance(user_id: int, amount: float) -> bool:
    """Check if the user has sufficient balance."""
    db = get_db()
    query = 'SELECT cashBalance FROM users WHERE userID = ?'
    balance = db.execute(query, (user_id,)).fetchone()['cashBalance']
    return float(balance) >= float(amount)


def add_to_balance(user_id: int, amount: float):
    """Add amount to the user's balance."""
    db = get_db()
    db.execute('UPDATE users SET cashBalance = cashBalance + ? WHERE userID = ?', (amount, user_id,))
    db.commit()


def get_last_price(stock_symbol: str) -> Optional[float]:
    """Retrieve the last closing price of the stock."""
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={stock_symbol}&outputsize=compact&apikey={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            day = data["Meta Data"]["3. Last Refreshed"]
            return float(data['Time Series (Daily)'][day]["4. close"])
    return None


def get_company_name(stock_symbol: str) -> Optional[str]:
    """Get the company name from the stock symbol."""
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={stock_symbol}&apikey={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200 and (data := response.json()):
        return data.get("Name")
    return None


def add_transaction(user_id: int, ticker: str, quantity: int, unit_price: float, total_price: float, order_type: str):
    """Record a new transaction."""
    db = get_db()
    db.execute(
        'INSERT INTO transactions(userID, ticker, amount, unitPrice, totalPrice, orderType, dateTime) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (user_id, ticker, quantity, unit_price, total_price, order_type, datetime.now())
    )
    db.commit()


def add_portfolio_object(user_id: int, ticker: str, quantity: int):
    """Add or update a stock in the user's portfolio."""
    db = get_db()
    if ticker_in_portfolio(user_id, ticker):
        db.execute('UPDATE PortfolioObjects SET quantity = quantity + ? WHERE userID = ? and ticker = ?',
                   (quantity, user_id, ticker,))
    else:
        db.execute('INSERT INTO PortfolioObjects(userID, ticker, quantity) VALUES (?, ?, ?)',
                   (user_id, ticker, quantity))
    db.commit()


def ticker_in_portfolio(user_id: int, ticker: str) -> bool:
    """Check if the ticker is already in the user's portfolio."""
    db = get_db()
    num_rows = \
    db.execute('SELECT count(*) FROM PortfolioObjects WHERE userID = ? and ticker = ?', (user_id, ticker,)).fetchone()[
        0]
    return num_rows > 0


def get_current_portfolio(user_id: int) -> List[Dict]:
    """Retrieve all portfolio objects for a user."""
    db = get_db()
    return db.execute('SELECT * FROM PortfolioObjects WHERE userID = ?', (user_id,)).fetchall()


def has_sufficient_stock(user_id: int, ticker: str, quantity: int) -> bool:
    """Check if the user has sufficient stock."""
    db = get_db()
    shares = db.execute('SELECT quantity FROM PortfolioObjects WHERE userID = ? and ticker = ?',
                        (user_id, ticker)).fetchone()
    return shares and int(shares['quantity']) >= quantity


def remove_portfolio_object(user_id: int, ticker: str, quantity: int):
    """Remove or decrease quantity of a stock in the user's portfolio."""
    db = get_db()
    db.execute('UPDATE PortfolioObjects SET quantity = quantity - ? WHERE userID = ? and ticker = ?',
               (quantity, user_id, ticker))
    db.commit()
    db.execute('DELETE FROM PortfolioObjects WHERE quantity <= 0')
    db.commit()
