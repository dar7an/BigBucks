import functools
from typing import Callable, Dict, List

from flask import (
    Blueprint, g, redirect, render_template, url_for
)

from .transactions import (
    get_current_portfolio,
    get_last_price, get_company_name
)

bp = Blueprint("home", __name__, url_prefix="/")


def login_required(view: Callable) -> Callable:
    """
    Decorator that redirects to the login page if the user is not logged in.

    Args:
    view (Callable): The view function to be decorated.

    Returns:
    Callable: The wrapped view function.
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@bp.route("/", methods=["GET", "POST"])
@login_required
def home() -> str:
    """
    View function for the homepage, displaying the user's portfolio.

    Returns:
    str: The rendered homepage template.
    """
    portfolio = get_current_portfolio(g.user['userID'])
    portfolio = format_portfolio(portfolio)
    return render_template("home.html", user=g.user, portfolio=portfolio)


def format_portfolio(input_portfolio: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Formats the raw portfolio data for display.

    Args:
    input_portfolio (List[Dict[str, str]]): The raw portfolio data from the database.

    Returns:
    List[Dict[str, str]]: A list of portfolio items with added details for display.
    """
    formatted_portfolio = []
    for item in input_portfolio:
        formatted_item = {
            'ticker': item['ticker'],
            'quantity': item['quantity'],
            'price': get_last_price(item['ticker']),
            'name': get_company_name(item['ticker'])
        }
        formatted_portfolio.append(formatted_item)
    return formatted_portfolio
