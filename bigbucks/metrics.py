import functools
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from .db import get_db
from .homepage import login_required
import sqlite3
import pandas as pd

bp = Blueprint("metrics", __name__, url_prefix="/metrics")

@bp.route("/metrics", methods=("GET", "POST"))
@login_required
def display_metrics():
    # Connect to the SQLite database
    db = get_db()

    # Get the portfolio for a specific user
    portfolio = pd.read_sql_query("SELECT ticker, quantity FROM PortfolioObjects WHERE userID = ?", db, params=(g.user['userID'],))

    # Fetch the historical price data for each stock in the portfolio
    price_data = []
    for ticker in portfolio['ticker']:
        data = pd.read_sql_query("SELECT closing_date, close_price FROM HistoricPriceData WHERE ticker = ?", db, params=(ticker,))
        data.set_index('closing_date', inplace=True)
        price_data.append(data)

    # Concatenate all price data into a single DataFrame
    df = pd.concat(price_data, axis=1)

    # Calculate the daily returns
    returns = df.pct_change()

    # Calculate the correlation matrix
    correlation_matrix = returns.corr()

    # Calculate the covariance matrix
    covariance_matrix = returns.cov()

    # Convert the matrices to a list of lists
    correlation_matrix_list = correlation_matrix.values.tolist()
    covariance_matrix_list = covariance_matrix.values.tolist()

    # Pass the matrices to the template
    return render_template("metrics/metrics.html", user=g.user, tickers=portfolio['ticker'].tolist(), correlation_matrix=correlation_matrix_list, covariance_matrix=covariance_matrix_list)
