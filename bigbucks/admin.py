from flask import Blueprint, render_template, g, redirect, url_for, flash
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

    # Retrieve all unique tickers and their quantity held across users
    unique_stocks = get_unique_stocks()
    if not unique_stocks:
        flash("Users have not purchased any stocks yet. Please check back later.")
        return redirect(url_for('admin.history'))

    stock_metrics = []
    risk_free_rate = get_risk_free_rate()

    for stock in unique_stocks:
        stock_data = calculate_stock_metrics(stock, risk_free_rate)
        if stock_data:  # Check if stock_data is not None before appending
            stock_metrics.append(stock_data)
        else:
            print(f"Metrics calculation failed for stock: {stock['ticker']}")

    if not stock_metrics:  # Check if list is empty
        flash("No valid stock metrics were calculated.")
        return redirect(url_for('admin.history'))

    portfolio_metrics = calculate_portfolio_metrics(stock_metrics, risk_free_rate)
    if not portfolio_metrics:
        flash("Failed to calculate portfolio metrics.")
        return redirect(url_for('admin.history'))

    return render_template('admin/risk_return.html', risk_return_data=stock_metrics, risk_free_rate=risk_free_rate,
                           portfolio_metrics=portfolio_metrics)


def get_unique_stocks():
    """Query database to find all unique stocks in the portfolios and their total quantities using get_db()."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            SELECT ticker, SUM(quantity) as total_quantity
            FROM PortfolioObjects
            GROUP BY ticker
        """)
        stocks = cursor.fetchall()
        return [{'ticker': stock[0], 'total_quantity': stock[1]} for stock in stocks]
    except Exception as e:
        # Log the error here
        print(f"Database error: {e}")
        return []
    finally:
        cursor.close()
