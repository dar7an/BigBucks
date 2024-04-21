import json

import requests
from flask import (
    Blueprint, jsonify, render_template, request
)

from .config import API_KEY
from .db import get_db

bp = Blueprint('search', __name__)


@bp.route('/config')
def config():
    return jsonify({'API_KEY': API_KEY})


@bp.route('/search')
def search():
    return render_template('search/search.html')


@bp.route('/stock_info', methods=('GET', 'POST'))
def stock_info():
    stock_symbol = request.form['stock_symbol']
    if get_stock_data_db(stock_symbol) != "null":
        return render_template('search/search_with_api.html', stock_symbol=stock_symbol,
                               corestock=get_global_quote(stock_symbol), overview=get_overview(stock_symbol),
                               news=get_news(stock_symbol), stock_data=get_stock_data_db(stock_symbol))
    else:
        if stock_exists(stock_symbol):
            pass
        else:
            insert_stock_data_db(stock_symbol)

        return render_template('search/search_with_db.html', stock_symbol=stock_symbol,
                               corestock=get_global_quote(stock_symbol), overview=get_overview(stock_symbol),
                               news=get_news(stock_symbol))


def get_global_quote(stock_symbol):
    url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=demo'
    url_with_apikey = url.replace('demo', API_KEY)
    url_with_symbol = url_with_apikey.replace('IBM', stock_symbol)
    r = requests.get(url_with_symbol)
    data = r.json()
    return data


def get_overview(stock_symbol):
    url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=IBM&apikey=demo'
    url_with_apikey = url.replace('demo', API_KEY)
    url_with_symbol = url_with_apikey.replace('IBM', stock_symbol)
    r = requests.get(url_with_symbol)
    data = r.json()
    return data


def get_news(stock_symbol):
    url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=IBM&apikey=demo'
    url_with_apikey = url.replace('demo', API_KEY)
    url_with_symbol = url_with_apikey.replace('IBM', stock_symbol)
    r = requests.get(url_with_symbol)
    data = r.json()
    return data


def get_trading_history_daily(stock_symbol):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&outputsize=full&apikey=demo'
    url_with_apikey = url.replace('demo', API_KEY)
    url_with_symbol = url_with_apikey.replace('IBM', stock_symbol)
    r = requests.get(url_with_symbol)
    data = r.json()
    return data


def get_stock_data_db(stock_symbol):
    db = get_db()
    stock_dict = {}
    stock_data_db = db.execute('SELECT * FROM HistoricPriceData WHERE ticker = ?', (stock_symbol,))
    sql3_rows = stock_data_db.fetchall()

    if len(sql3_rows) == 0:
        stock_dict_json = "null"
        return stock_dict_json

    for data in sql3_rows:
        stock_symbol = data[0]
        closing_date = data[1]

        if stock_symbol not in stock_dict:
            stock_dict[stock_symbol] = {}

        closing_date_str = closing_date.isoformat()

        stock_dict[stock_symbol][closing_date_str] = {
            "close_price": data["close_price"],
            # add other functionalities later...
        }
    stock_dict_json = json.dumps(stock_dict)

    return stock_dict_json


def insert_stock_data_db(stock_symbol):
    db = get_db()
    data = get_trading_history_daily(stock_symbol)
    if data:
        for date, date_data in data["Time Series (Daily)"].items():
            close_price = date_data["4. close"]
            print(stock_symbol)
            print(date)
            print(close_price)
            db.execute("DELETE FROM HistoricPriceData WHERE ticker = ?", (stock_symbol,))
            db.execute(
                "INSERT INTO HistoricPriceData (ticker, closing_date, open_price, "
                "high_price, low_price, close_price, adj_close_price, volume) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    stock_symbol,
                    date,
                    0,
                    0,
                    0,
                    close_price,
                    0,
                    0
                )
            )
        db.commit()
    else:
        print(f"Error: 'Time Series (Daily)' key not found in data for stock symbol {stock_symbol}")


def stock_exists(stock_symbol):
    db = get_db()
    result = db.execute('SELECT * FROM HistoricPriceData WHERE ticker = ?', (stock_symbol,))
    return result.fetchone() is not None


def get_10_year_treasury():
    url = 'https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity=10year&apikey=demo'
    url_with_apikey = url.replace('demo', API_KEY)
    r = requests.get(url_with_apikey)
    data = r.json()
    return data


def get_SPY():
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SPY&outputsize=full&apikey=demo'
    url_with_apikey = url.replace('demo', API_KEY)
    r = requests.get(url_with_apikey)
    data = r.json()
    return data


def update_SPY():
    insert_stock_data_db('SPY')
    return None
