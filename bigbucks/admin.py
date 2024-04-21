import numpy as np
from flask import Blueprint, render_template, g
from werkzeug.exceptions import abort
from datetime import datetime
from .db import get_db
from .home import login_required
from .transactions import get_company_name, update_portfolio_data, get_current_portfolio

bp = Blueprint('admin', __name__, url_prefix='/admin')


def check_admin():
    if g.user is None or g.user['role'] != 'admin':
        abort(403)


def get_users():
    db = get_db()
    users = db.execute('SELECT * FROM Users').fetchall()
    return users


@bp.route('/history')
@login_required
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
        stock_name = get_company_name(portfolio_object['ticker'])
        history_data.append({
            'ticker': portfolio_object['ticker'],
            'name': stock_name,
            'total_shares_held': portfolio_object['total_shares_held'],
            'price_per_share': portfolio_object['price_per_share']
        })

    return render_template('admin/history.html', history_data=history_data)


@bp.route('/summary')
@login_required
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
        stock_name = get_company_name(transaction['ticker'])
        summary_data.append({
            'ticker': transaction['ticker'],
            'name': stock_name,
            'shares_bought': transaction['shares_bought'],
            'shares_sold': transaction['shares_sold']
        })

    return render_template('admin/summary.html', summary_data=summary_data, current_date=current_date)


@bp.route('/risk_return')
@login_required
def risk_return():
    check_admin()
    db = get_db()

    # Get all users
    users = get_users()

    # Calculate risk-return metrics for each user's portfolio
    risk_return_data = []
    for user in users:
        user_id = user['userID']
        update_portfolio_data(user_id)  # Update stock data for the user's portfolio
        portfolio = get_current_portfolio(user_id)

        for stock in portfolio:
            stock_data = calculate_stock_metrics(db, stock)
            risk_return_data.append(stock_data)

    return render_template('admin/risk_return.html', risk_return_data=risk_return_data)


def calculate_stock_metrics(db, stock):
    ticker = stock['ticker']
    quantity = stock['quantity']

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

    # Calculate beta
    beta = np.cov(returns, np.full(len(returns), market_returns))[0][1] / np.var(np.full(len(returns), market_returns))

    # Calculate Sharpe and Treynor ratios
    risk_free_rate = 0.02
    mean_returns = np.mean(returns)
    excess_returns = returns - risk_free_rate
    sharpe_ratio = np.mean(excess_returns) / np.std(returns)
    treynor_ratio = mean_returns / beta

    return {
        'user_id': stock['userID'],
        'ticker': ticker,
        'quantity': quantity,
        'beta': beta,
        'sharpe_ratio': sharpe_ratio,
        'treynor_ratio': treynor_ratio
    }
