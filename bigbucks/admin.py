import requests
from .config import API_KEY
from flask import Blueprint, render_template, g
from werkzeug.exceptions import abort
from datetime import datetime, timedelta
from .db import get_db

bp = Blueprint('admin', __name__, url_prefix='/admin')


def check_admin():
    if g.user is None or g.user['role'] != 'admin':
        abort(403)


def get_stock_name(stock_symbol):
    url = requests.get(f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={stock_symbol}&apikey={API_KEY}')
    data = url.json()
    return data.get('Name')


@bp.route('/history')
def history():
    check_admin()
    db = get_db()
    portfolio_objects = db.execute("""
    SELECT po.ticker, SUM(po.quantity) AS total_shares_held, t.unitPrice AS price_per_share
    FROM PortfolioObjects po
    JOIN Transactions t ON po.ticker = t.ticker
    GROUP BY po.ticker
    ORDER BY po.ticker;
    """).fetchall()

    history_data = []
    for portfolio_object in portfolio_objects:
        stock_name = get_stock_name(portfolio_object['ticker'])
        history_data.append({
            'ticker': portfolio_object['ticker'],
            'name': stock_name,
            'total_shares_held': portfolio_object['total_shares_held'],
            'price_per_share': portfolio_object['price_per_share']
        })

    return render_template('admin/history.html', history_data=history_data)


@bp.route('/summary')
def summary():
    check_admin()
    db = get_db()
    current_date = datetime.now().strftime('%Y-%m-%d')
    transactions = db.execute("""
    SELECT t.ticker,
           SUM(CASE WHEN t.orderType = 'buy' THEN t.amount ELSE 0 END) AS shares_bought,
           SUM(CASE WHEN t.orderType = 'sell' THEN t.amount ELSE 0 END) AS shares_sold
    FROM Transactions t
    WHERE DATE(t.dateTime) = ?
    GROUP BY t.ticker
    ORDER BY t.ticker;
    """, (current_date,)).fetchall()

    summary_data = []
    for transaction in transactions:
        stock_name = get_stock_name(transaction['ticker'])
        summary_data.append({
            'ticker': transaction['ticker'],
            'name': stock_name,
            'shares_bought': transaction['shares_bought'],
            'shares_sold': transaction['shares_sold']
        })

    return render_template('admin/summary.html', summary_data=summary_data, current_date=current_date)


@bp.route('/risk_return')
def risk_return():
    check_admin()
    db = get_db()
    stocks = db.execute("""
    SELECT DISTINCT ticker
    FROM PortfolioObjects;
    """).fetchall()

    # Convert stock records to ticker symbols
    ticker_symbols = [stock['ticker'] for stock in stocks]
    ticker_string = ','.join(ticker_symbols)

    # Prepare date range for API call
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5 * 365)).strftime('%Y-%m-%d')

    # Fetch data from AlphaVantage API for all stocks
    url = (
        f'https://alphavantageapi.co/timeseries/analytics?SYMBOLS={ticker_string}&RANGE={start_date}&RANGE={end_date}&INTERVAL=DAILY&OHLC=close&CALCULATIONS=MEAN,STDDEV&apikey={API_KEY}'
    )
    response = requests.get(url)
    data = response.json()
    # print(data)

    # Initialize list to hold risk-return data
    risk_return_data = []

    # Iterate over stocks to extract their mean return and standard deviation
    for stock in stocks:
        mean_return = data['payload']['RETURNS_CALCULATIONS']['MEAN'].get(stock['ticker'])
        risk = data['payload']['RETURNS_CALCULATIONS']['STDDEV'].get(stock['ticker'])

        if mean_return is not None and risk is not None:
            risk_return_data.append({
                'ticker': stock['ticker'],
                'return': mean_return,
                'risk': risk,
            })

    print(risk_return_data)
    return render_template('admin/risk_return.html', risk_return_data=risk_return_data)
