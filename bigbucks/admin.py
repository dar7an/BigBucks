from flask import Blueprint, render_template, g
from werkzeug.exceptions import abort
from datetime import datetime

from .db import get_db
from .home import login_required
from .transactions import get_company_name, update_portfolio_data, get_current_portfolio, calculate_stock_metrics, \
    get_risk_free_rate, calculate_portfolio_metrics

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

    # Get all users
    users = get_users()

    # Calculate risk-return metrics for each user's portfolio
    stock_metrics = []
    portfolio_metrics = {}
    risk_free_rate = get_risk_free_rate()  # Risk-free rate
    for user in users:
        user_id = user['userID']
        portfolio = get_current_portfolio(user_id)
        update_portfolio_data(user_id)  # Update stock data for the user's portfolio

        for stock in portfolio:
            stock_data = calculate_stock_metrics(stock, risk_free_rate)
            stock_metrics.append(stock_data)

    # Calculate average beta, Sharpe ratio, and Treynor ratio
    portfolio_metrics = calculate_portfolio_metrics(stock_metrics, risk_free_rate)

    return render_template('admin/risk_return.html',
                           risk_return_data=stock_metrics,
                           risk_free_rate=risk_free_rate,
                           portfolio_metrics=portfolio_metrics)
