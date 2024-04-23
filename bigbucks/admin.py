from flask import Blueprint, render_template, g, redirect, url_for, flash
from werkzeug.exceptions import abort
from datetime import datetime

from .db import get_db
from .home import login_required
from .search import get_10_year_treasury
from .solver import Asset, Solver
from .transactions import get_company_name, update_portfolio_data, get_current_portfolio, calculate_stock_metrics, \
    get_risk_free_rate, calculate_portfolio_metrics

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

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

    users = db.execute('SELECT * FROM Users').fetchall()

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

    return render_template('admin/summary.html', summary_data=summary_data, current_date=current_date, users=users)


@bp.route('/risk_return')
@login_required
def risk_return():
    check_admin()
    # Get the user's portfolio
    db = get_db()

    portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects", db)

    if len(portfolio['ticker'].unique()) < 2:
        flash("Metrics are unavailable. Less than 2 stocks in the system.")
        return redirect(url_for('admin.summary'))

    # Get the risk free rate
    risk_free_rate = get_10_year_treasury()
    risk_free_rate = float(risk_free_rate['data'][0]['value']) * .01

    # First loop for creating data
    data_list = []
    for ticker in portfolio['ticker']:
        data = pd.read_sql_query("SELECT closing_date, close_price FROM HistoricPriceData WHERE ticker = ?"
                                 , db, params=(ticker,))
        data.set_index('closing_date', inplace=True)
        data = pd.DataFrame(data)
        data_list.append(data)

    # Limiting data calculation to the last five years
    for i in range(len(data_list)):
        data_list[i] = data_list[i].dropna()
        one_years_ago = (datetime.now() - timedelta(days= 365)).date()
        data_list[i] = data_list[i][data_list[i].index >= one_years_ago]

    # Second loop for creating price_data and asset_vector
    price_data = []
    asset_vector = []
    for ticker, data in zip(portfolio['ticker'], data_list):
        price_data.append(data)
        asset = Asset(ticker, data)
        asset_vector.append(asset)

    df = pd.concat(price_data, axis=1, keys=[asset.ticker for asset in asset_vector])

    # Returns in decimal. For instance, 10% is 0.1
    returns = df.pct_change(fill_method=None)

    correlation_matrix = pd.DataFrame(returns.corr())
    covariance_matrix = pd.DataFrame(returns.cov())
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()

    # Calculating total value of portfolio
    totalvalue = 0
    totalvalue_vector = []
    for ticker in portfolio['ticker']:
        transaction_value_temp = pd.read_sql_query("SELECT totalPrice FROM Transactions WHERE ticker = ?", db,
                                                   params=(ticker,))
        totalvalue = transaction_value_temp + totalvalue
        totalvalue_vector.append(transaction_value_temp.iloc[0].item())

    # Finding weights of each asset in the portfolio
    weight_vector = []
    for transaction_value in totalvalue_vector:
        transaction_weight = transaction_value / totalvalue
        transaction_weight = transaction_weight.iloc[0, 0]
        weight_vector.append(transaction_weight)

    # Calculating portfolio return and volatility
    total_returns = returns.sum()
    total_portfolio_return = sum([a * b for a, b in zip(total_returns, weight_vector)])
    portfolio_vol = Solver()
    portfolio_volatility = portfolio_vol.compute(covariance_matrix, asset_vector, total_portfolio_return)
    portfolio_weight = portfolio_vol.compute_weights()

    # Calculating Sharpe Ratio
    sharpe_ratio = ((total_portfolio_return - risk_free_rate) / (portfolio_volatility * 100))

    # Calculating volatility for different returns, for effiecent frontier to be plotted
    solver = Solver()
    returns_vector = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
                      0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3,
                      1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0]
    volatilities = []
    for a_return in returns_vector:
        volatility = solver.compute(covariance_matrix, asset_vector, a_return)
        volatilities.append(volatility)

    # Creating a list of tuples for returns and volatilities for effiecent frontier to be plotted
    returns_volatilities = list(zip(returns_vector, volatilities))

    return render_template("admin/risk_return.html", user=g.user, tickers=portfolio['ticker'].tolist()
                           , correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list
                           , returns_volatilities=returns_volatilities, sharpe_ratio=sharpe_ratio.item(),
                           portfolio_return=total_portfolio_return, portfolio_volatility=portfolio_volatility,
                           weight_vector=weight_vector)

    # # Retrieve all unique tickers and their quantity held across users
    # unique_stocks = get_unique_stocks()
    # if not unique_stocks:
    #     flash("Users have not purchased any stocks yet. Please check back later.")
    #     return redirect(url_for('admin.history'))

    # stock_metrics = []
    # risk_free_rate = get_risk_free_rate()

    # for stock in unique_stocks:
    #     stock_data = calculate_stock_metrics(stock, risk_free_rate)
    #     if stock_data:  # Check if stock_data is not None before appending
    #         stock_metrics.append(stock_data)
    #     else:
    #         print(f"Metrics calculation failed for stock: {stock['ticker']}")

    # if not stock_metrics:  # Check if list is empty
    #     flash("No valid stock metrics were calculated.")
    #     return redirect(url_for('admin.history'))

    # portfolio_metrics = calculate_portfolio_metrics(stock_metrics, risk_free_rate)
    # if not portfolio_metrics:
    #     flash("Failed to calculate portfolio metrics.")
    #     return redirect(url_for('admin.history'))

    # return render_template('admin/risk_return.html', risk_return_data=stock_metrics, risk_free_rate=risk_free_rate,
    #                        portfolio_metrics=portfolio_metrics)


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


@bp.route('/summary/<string:userID>', methods=['GET'])
def display_user_matrices(userID):
    db = get_db()

    # Get the user's portfolio
    portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects WHERE userID = ?"
                                  , db, params=(userID,))

    if len(portfolio) < 2:
        flash("You need at least 2 stocks in your portfolio to view metrics.")
        return redirect(url_for('admin.summary'))

    # Get the risk free rate
    risk_free_rate = get_10_year_treasury()
    risk_free_rate = float(risk_free_rate['data'][0]['value']) * .01

    # First loop for creating data
    data_list = []
    for ticker in portfolio['ticker']:
        data = pd.read_sql_query("SELECT closing_date, close_price FROM HistoricPriceData WHERE ticker = ?"
                                 , db, params=(ticker,))
        data.set_index('closing_date', inplace=True)
        data = pd.DataFrame(data)
        data_list.append(data)

    # Limiting data calculation to the last five years
    for i in range(len(data_list)):
        data_list[i] = data_list[i].dropna()
        one_years_ago = (datetime.now() - timedelta(days= 365)).date()
        data_list[i] = data_list[i][data_list[i].index >= one_years_ago]

    # Second loop for creating price_data and asset_vector
    price_data = []
    asset_vector = []
    for ticker, data in zip(portfolio['ticker'], data_list):
        price_data.append(data)
        asset = Asset(ticker, data)
        asset_vector.append(asset)

    df = pd.concat(price_data, axis=1, keys=[asset.ticker for asset in asset_vector])

    # Returns in decimal. For instance, 10% is 0.1
    returns = df.pct_change(fill_method=None)

    correlation_matrix = pd.DataFrame(returns.corr())
    covariance_matrix = pd.DataFrame(returns.cov())
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()

    # Calculating total value of portfolio
    totalvalue = 0
    totalvalue_vector = []
    for ticker in portfolio['ticker']:
        transaction_value_temp = pd.read_sql_query("SELECT totalPrice FROM Transactions WHERE ticker = ?", db,
                                                   params=(ticker,))
        totalvalue = transaction_value_temp + totalvalue
        totalvalue_vector.append(transaction_value_temp.iloc[0].item())

    # Finding weights of each asset in the portfolio
    weight_vector = []
    for transaction_value in totalvalue_vector:
        transaction_weight = transaction_value / totalvalue
        transaction_weight = transaction_weight.iloc[0, 0]
        weight_vector.append(transaction_weight)

    # Calculating portfolio return and volatility
    total_returns = returns.sum()
    total_portfolio_return = sum([a * b for a, b in zip(total_returns, weight_vector)])
    portfolio_vol = Solver()
    portfolio_volatility = portfolio_vol.compute(covariance_matrix, asset_vector, total_portfolio_return)
    portfolio_weight = portfolio_vol.compute_weights()

    # Calculating Sharpe Ratio
    sharpe_ratio = ((total_portfolio_return - risk_free_rate) / (portfolio_volatility * 100))

    # Calculating volatility for different returns, for effiecent frontier to be plotted
    solver = Solver()
    returns_vector = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
                      0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3,
                      1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0]
    volatilities = []
    for a_return in returns_vector:
        volatility = solver.compute(covariance_matrix, asset_vector, a_return)
        volatilities.append(volatility)

    # Creating a list of tuples for returns and volatilities for effiecent frontier to be plotted
    returns_volatilities = list(zip(returns_vector, volatilities))

    return render_template("admin/user_metrics.html", user=g.user, tickers=portfolio['ticker'].tolist()
                           , correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list
                           , returns_volatilities=returns_volatilities, sharpe_ratio=sharpe_ratio.item(),
                           portfolio_return=total_portfolio_return, portfolio_volatility=portfolio_volatility,
                           weight_vector=weight_vector)
