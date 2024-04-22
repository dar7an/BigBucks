from typing import Optional, List, Dict

import numpy as np

from .db import get_db
from .config import API_KEY
import requests
from datetime import datetime, timedelta


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
        db.execute('SELECT count(*) FROM PortfolioObjects WHERE userID = ? and ticker = ?',
                   (user_id, ticker,)).fetchone()[
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


def update_stock_data(ticker):
    # Set the endpoint and parameters for the API call
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": ticker,
        "outputsize": "full",
        "apikey": API_KEY
    }

    # Make the API request
    response = requests.get(url, params=params)
    data = response.json()

    # Parse the JSON data
    time_series = data['Time Series (Daily)']
    records = []
    five_years_ago = datetime.now() - timedelta(days=5 * 365)
    for date, values in time_series.items():
        record_date = datetime.strptime(date, '%Y-%m-%d')
        if record_date >= five_years_ago:  # Only include data within the last 5 years
            record = (
                ticker,
                date,
                values['1. open'],
                values['2. high'],
                values['3. low'],
                values['4. close'],
                values['5. adjusted close'],
                values['6. volume']
            )
            records.append(record)

    # Connect to the database
    db = get_db()
    cursor = db.cursor()

    # Get the most recent date from the database
    cursor.execute("SELECT MAX(closing_date) FROM HistoricPriceData WHERE ticker = ?", (ticker,))
    last_date = cursor.fetchone()[0]
    last_date = datetime.strptime(last_date, '%Y-%m-%d') if last_date else datetime.now() - timedelta(days=5 * 365)

    # Filter new records to be inserted
    new_records = [record for record in records if datetime.strptime(record[1], '%Y-%m-%d') > last_date]

    # Insert new records into the database
    if new_records:
        cursor.executemany('''
            INSERT INTO HistoricPriceData 
            (ticker, closing_date, open_price, high_price, low_price, close_price, adj_close_price, volume) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', new_records)
        db.commit()


def delete_stock_data(ticker):
    # Connect to the database
    db = get_db()
    cursor = db.cursor()

    # Check if any user still owns the stock
    cursor.execute("SELECT COUNT(*) FROM PortfolioObjects WHERE ticker = ?", (ticker,))
    count = cursor.fetchone()[0]

    if count > 0:
        # If any user still owns the stock, do not delete the historical data
        pass
    else:
        # Delete all historical data for the given ticker
        cursor.execute("DELETE FROM HistoricPriceData WHERE ticker = ?", (ticker,))
        db.commit()


def update_portfolio_data(user_id: int):
    """Update stock data for all stocks in the user's portfolio."""
    portfolio = get_current_portfolio(user_id)
    for stock in portfolio:
        update_stock_data(stock['ticker'])


def calculate_stock_metrics(stock, risk_free_rate):
    ticker = stock['ticker']
    quantity = stock['quantity']

    db = get_db()

    # Retrieve historical price data for the stock (last 3 years)
    historical_data = db.execute("""
        SELECT closing_date, adj_close_price
        FROM HistoricPriceData
        WHERE ticker = ? AND closing_date >= DATE('now', '-3 years')
        ORDER BY closing_date
    """, (ticker,)).fetchall()

    if not historical_data:
        return None

    adj_close_prices = np.array([data['adj_close_price'] for data in historical_data])

    # Calculate daily returns
    returns = np.diff(adj_close_prices) / adj_close_prices[:-1]

    # Market returns (placeholder)
    market_returns = np.mean(returns)

    # Calculate Standard Deviation
    std_dev = np.std(returns)

    # Calculate beta
    beta = np.cov(returns, np.full(len(returns), market_returns))[0][1] / np.var(np.full(len(returns), market_returns))

    # Calculate Sharpe and Treynor ratios
    mean_returns = np.mean(returns)
    excess_returns = returns - risk_free_rate
    sharpe_ratio = np.mean(excess_returns) / np.std(returns)
    treynor_ratio = mean_returns / beta

    return {
        'ticker': ticker,
        'quantity': quantity,
        'beta': beta,
        'sharpe_ratio': sharpe_ratio,
        'treynor_ratio': treynor_ratio,
        'current_price': adj_close_prices[-1],
        'mean_returns': mean_returns,
        'std_dev': std_dev
    }


def calculate_portfolio_metrics(stock_metrics, risk_free_rate):
    # Initialize accumulators for weighted metrics
    total_value = 0
    weighted_beta = 0
    weighted_returns = 0
    total_sharpe_numerator = 0
    total_sharpe_denominator = 0

    # Process each stock's metrics
    for metrics in stock_metrics:
        # Extract required data
        current_price = metrics['current_price']  # Assume current price is part of metrics
        total_quantity = metrics['quantity']
        stock_value = total_quantity * current_price
        total_value += stock_value

        # Accumulate weighted metrics
        weighted_beta += metrics['beta'] * stock_value
        weighted_returns += metrics['mean_returns'] * stock_value
        total_sharpe_numerator += (metrics['mean_returns'] - risk_free_rate) * total_quantity
        total_sharpe_denominator += np.power(metrics['std_dev'], 2) * total_quantity

    if total_value == 0:
        return None

    # Normalize weighted sums
    portfolio_beta = weighted_beta / total_value
    portfolio_mean_returns = weighted_returns / total_value
    portfolio_sharpe_ratio = total_sharpe_numerator / np.sqrt(total_sharpe_denominator)
    portfolio_treynor_ratio = portfolio_mean_returns / portfolio_beta

    return {
        'beta': portfolio_beta,
        'sharpe_ratio': portfolio_sharpe_ratio,
        'treynor_ratio': portfolio_treynor_ratio
    }


def get_risk_free_rate():
    """Fetch the latest 10-Year Treasury Constant Maturity Rate from Alpha Vantage API."""
    url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&apikey={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if data['data']:
            latest_rate = float(data['data'][0]['value'])
            return latest_rate / 100  # Convert percent to decimal
        else:
            return None
    else:
        return None
