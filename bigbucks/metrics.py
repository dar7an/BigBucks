from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from datetime import datetime, timedelta
from .db import get_db
from .homepage import login_required
from .solver import Solver, Asset
from .stocksearch import get_10_year_treasury
import pandas as pd
import numpy as np

bp = Blueprint("metrics", __name__, url_prefix="/metrics")

@bp.route("/metrics", methods=("GET", "POST"))
@login_required
def display_matrices():
    # Get the risk free rate
    risk_free_rate = get_10_year_treasury()
    risk_free_rate = float(risk_free_rate['data'][0]['value'])*.01

    # Get the user's portfolio
    db = get_db()
    portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects WHERE userID = ?"
                                  , db, params=(g.user['userID'],))

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
        one_years_ago = (datetime.now() - timedelta(days=5*365)).date()
        data_list[i] = data_list[i][data_list[i].index >= one_years_ago]
    
    # Second loop for creating price_data and asset_vector
    price_data = []
    asset_vector = []
    for ticker, data in zip(portfolio['ticker'], data_list):
        price_data.append(data)
        asset = Asset(ticker, data)
        asset_vector.append(asset)

    df = pd.concat(price_data, axis=1, keys=[asset.ticker for asset in asset_vector])

    #Returns in decimal. For instance, 10% is 0.1
    returns = df.pct_change(fill_method=None)

    correlation_matrix = pd.DataFrame(returns.corr())
    covariance_matrix = pd.DataFrame(returns.cov())
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()
    
    #Calculating total value of portfolio
    totalvalue = 0
    totalvalue_vector = []
    for ticker in portfolio['ticker']:
        transaction_value_temp = pd.read_sql_query("SELECT totalPrice FROM Transactions WHERE ticker = ?", db, params=(ticker,))
        totalvalue = transaction_value_temp + totalvalue
        totalvalue_vector.append(transaction_value_temp.iloc[0].item())
        
    #Finding weights of each asset in the portfolio
    weight_vector = []
    for transaction_value in totalvalue_vector:
        transaction_weight = transaction_value / totalvalue
        transaction_weight = transaction_weight.iloc[0,0]
        weight_vector.append(transaction_weight)
        
    #Calculating portfolio return and volatility
    total_returns = returns.sum()
    total_portfolio_return = sum([a*b for a, b in zip(total_returns, weight_vector)])
    portfolio_vol = Solver()
    portfolio_volatility = portfolio_vol.compute(covariance_matrix, asset_vector, total_portfolio_return)
    portfolio_weight = portfolio_vol.compute_weights()
    print("This is the portfolio weight: " + str(portfolio_weight))
    
    #Calculating Sharpe Ratio
    print("This is the total portfolio return: " + str(total_portfolio_return))
    print("This is the risk free rate: " + str(risk_free_rate))
    print("This is the portfolio volatility: " + str(portfolio_volatility))
    sharpe_ratio = ((total_portfolio_return-risk_free_rate) / (portfolio_volatility*100))
    print("This is the sharpe ratio: " + str(sharpe_ratio))
    
    #Calculating volatility for different returns, for effiecent frontier to be plotted
    solver = Solver()
    returns_vector = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 
                      0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 
                      1.35, 1.4, 1.45, 1.5, 1.55, 1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0]
    volatilities = []
    for a_return in returns_vector:
        volatility = solver.compute(covariance_matrix, asset_vector, a_return)
        volatilities.append(volatility)

    #Creating a list of tuples for returns and volatilities for effiecent frontier to be plotted
    returns_volatilities = list(zip(returns_vector, volatilities))
    
    return render_template("metrics/metrics.html", user=g.user, tickers=portfolio['ticker'].tolist()
                        , correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list
                        , returns_volatilities=returns_volatilities, sharpe_ratio=sharpe_ratio, 
                        portfolio_return=total_portfolio_return, portfolio_volatility=portfolio_volatility,
                        weight_vector=weight_vector)
