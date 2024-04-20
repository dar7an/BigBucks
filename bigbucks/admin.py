import requests
from .config import API_KEY
from flask import Blueprint, app, render_template, g  
from werkzeug.exceptions import abort
from datetime import datetime, timedelta
from .db import get_db
from .homepage import login_required
import pandas as pd
from .solver import Solver, Asset
from .stocksearch import get_10_year_treasury

bp = Blueprint('admin', __name__, url_prefix='/admin')


def check_admin():
    if g.user is None or g.user['role'] != 'admin':
        abort(403)

def get_stock_name(stock_symbol):
    url = requests.get(f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={stock_symbol}&apikey={API_KEY}')
    data = url.json()
    return data.get('Name')

def get_users():
    db = get_db()
    users = db.execute('SELECT * FROM Users').fetchall()
    # for user in users:
    #     print(user['userID'])
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
        stock_name = get_stock_name(portfolio_object['ticker'])
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
        stock_name = get_stock_name(transaction['ticker'])
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
    risk_free_rate = get_10_year_treasury()
    risk_free_rate = float(risk_free_rate['data'][0]['value'])*.01
    db = get_db()
    users = get_users()
    aggregated_portfolio = pd.DataFrame()
    for user in users:
        portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects WHERE userID = ?"
                                    , db, params=(user['UserID'],))
        aggregated_portfolio = pd.concat([aggregated_portfolio, portfolio], ignore_index=True)
        
    aggregated_portfolio = aggregated_portfolio.groupby('ticker').sum().reset_index()

    price_data = []
    asset_vector = []
    from datetime import datetime, timedelta

    five_years_ago = datetime.now() - timedelta(days=5*365)

    for ticker in aggregated_portfolio['ticker']:
        data = pd.read_sql_query("SELECT closing_date, close_price FROM HistoricPriceData WHERE ticker = ? AND closing_date >= ?"
                                 , db, params=(ticker, five_years_ago))
        data.set_index('closing_date', inplace=True)
        data = pd.DataFrame(data) 
        price_data.append(data)
        asset = Asset(ticker,data)  
        asset_vector.append(asset)

    df = pd.concat(price_data, axis=1, keys=[asset.ticker for asset in asset_vector])
    
    returns = df.pct_change()
    correlation_matrix = pd.DataFrame(returns.corr())
    covariance_matrix = pd.DataFrame(returns.cov())
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()
    
    totalvalue = 0
    totalvalue_vector = []
    for ticker in aggregated_portfolio['ticker']:
        transaction_value_temp = pd.read_sql_query("SELECT totalPrice FROM Transactions WHERE ticker = ?", db, params=(ticker,))
        totalvalue = transaction_value_temp + totalvalue
        totalvalue_vector.append(transaction_value_temp.iloc[0].item())
        
    weight_vector = []
    for transaction_value in totalvalue_vector:
        transaction_weight = transaction_value / totalvalue
        transaction_weight = transaction_weight.iloc[0,0]
        weight_vector.append(transaction_weight)

    total_portfolio_return = sum([a*b for a, b in zip(returns.mean(), weight_vector)])
    portfolio_vol = Solver()
    portfolio_volatility = portfolio_vol.compute(covariance_matrix, asset_vector, total_portfolio_return)
    
    sharpe_ratio = ((total_portfolio_return-risk_free_rate) / portfolio_volatility)
    
    solver = Solver()
    returns_vector = [0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1
                      ,.11,.12,.13,.14,.15,.16,.17,.18,.19,.2,.21,.22,.23,.24,.25,.26]
    volatilities = []
    for a_return in returns_vector:
        volatility = solver.compute(correlation_matrix, asset_vector, a_return)
        volatilities.append(volatility)

    returns_volatilities = list(zip(returns_vector, volatilities))
    return render_template("admin/risk_return.html", user=g.user, tickers=aggregated_portfolio['ticker'].tolist()
                    , correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list
                    , returns_volatilities=returns_volatilities, sharpe_ratio=sharpe_ratio)