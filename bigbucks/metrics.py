import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .db import get_db
from .homepage import login_required
from .solver import Solver, Asset
import pandas as pd

bp = Blueprint("metrics", __name__, url_prefix="/metrics")

@bp.route("/metrics", methods=("GET", "POST"))
@login_required
def display_matrices():
    db = get_db()
    portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects WHERE userID = ?"
                                  , db, params=(g.user['userID'],))

    price_data = []
    asset_vector = []
    for ticker in portfolio['ticker']:
        data = pd.read_sql_query("SELECT closing_date, close_price FROM HistoricPriceData WHERE ticker = ?"
                                 , db, params=(ticker,))
        data.set_index('closing_date', inplace=True)
        data = pd.DataFrame(data)   
        price_data.append(data)
        asset = Asset(ticker,data)  # This is the Asset class from solver.py
        asset_vector.append(asset)

    df = pd.concat(price_data, axis=1, keys=[asset.ticker for asset in asset_vector])
    returns = df.pct_change()
    correlation_matrix = pd.DataFrame(returns.corr())
    covariance_matrix = pd.DataFrame(returns.cov())
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()
    
    solver = Solver()
    returns_vector = [0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1
                      ,.11,.12,.13,.14,.15,.16,.17,.18,.19,.2,.21,.22,.23,.24,.25,.26]
    volatilities = []
    for a_return in returns_vector:
        volatility = solver.compute(correlation_matrix, asset_vector, a_return)
        volatilities.append(volatility)

    returns_volatilities = list(zip(returns_vector, volatilities))
    return render_template("metrics/metrics.html", user=g.user, tickers=portfolio['ticker'].tolist()
                           , correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list
                           , returns_volatilities=returns_volatilities)
