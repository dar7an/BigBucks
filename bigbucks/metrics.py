import pandas as pd
from flask import Blueprint, g, render_template, flash, redirect, url_for

from .db import get_db
from .home import login_required
from .search import get_10_year_treasury
from .solver import Solver, Asset

bp = Blueprint("metrics", __name__, url_prefix="/metrics")


@bp.route("/metrics", methods=("GET", "POST"))
@login_required
def display_matrices():
    risk_free_rate = get_10_year_treasury()
    risk_free_rate = float(risk_free_rate['data'][0]['value']) * .01
    db = get_db()

    portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects WHERE userID = ?"
                                  , db, params=(g.user['userID'],))

    # Check if the portfolio is empty
    if len(portfolio) < 2:
        flash('Portfolio is currently empty. Please add stocks to view metrics.')
        return redirect(url_for('trade.trade'))

    price_data = []
    asset_vector = []
    for ticker in portfolio['ticker']:
        data = pd.read_sql_query("SELECT closing_date, close_price FROM HistoricPriceData WHERE ticker = ?"
                                 , db, params=(ticker,))
        data.set_index('closing_date', inplace=True)
        data = pd.DataFrame(data)
        price_data.append(data)
        asset = Asset(ticker, data)
        asset_vector.append(asset)

    df = pd.concat(price_data, axis=1, keys=[asset.ticker for asset in asset_vector])
    returns = df.pct_change(fill_method=None)
    correlation_matrix = pd.DataFrame(returns.corr())
    covariance_matrix = pd.DataFrame(returns.cov())
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()

    totalvalue = 0
    totalvalue_vector = []
    for ticker in portfolio['ticker']:
        transaction_value_temp = pd.read_sql_query("SELECT totalPrice FROM Transactions WHERE ticker = ?", db,
                                                   params=(ticker,))
        totalvalue = transaction_value_temp + totalvalue
        totalvalue_vector.append(transaction_value_temp.iloc[0].item())

    weight_vector = []
    for transaction_value in totalvalue_vector:
        transaction_weight = transaction_value / totalvalue
        transaction_weight = transaction_weight.iloc[0, 0]
        weight_vector.append(transaction_weight)

    total_portfolio_return = sum([a * b for a, b in zip(returns.mean(), weight_vector)])
    portfolio_vol = Solver()
    portfolio_volatility = portfolio_vol.compute(covariance_matrix, asset_vector, total_portfolio_return)

    sharpe_ratio = ((total_portfolio_return - risk_free_rate) / portfolio_volatility)

    solver = Solver()
    returns_vector = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1
        , .11, .12, .13, .14, .15, .16, .17, .18, .19, .2, .21, .22, .23, .24, .25, .26]
    volatilities = []
    for a_return in returns_vector:
        volatility = solver.compute(correlation_matrix, asset_vector, a_return)
        volatilities.append(volatility)

    returns_volatilities = list(zip(returns_vector, volatilities))

    return render_template("metrics/metrics.html", user=g.user, tickers=portfolio['ticker'].tolist()
                           , correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list
                           , returns_volatilities=returns_volatilities, sharpe_ratio=sharpe_ratio)
