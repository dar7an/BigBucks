from .db import get_db


def hasSufficientBalance(userID, amount):
    # returns true if the user has balance greater than or equal to amount
    db = get_db()
    balance = db.execute(
        'SELECT cashBalance FROM users WHERE userID = ?',
        (userID,)
        ).fetchone()['cashBalance']

    if balance >= amount:
        return True
    return False


def addToBalance(userID, amount):
    # adds amount to user's balance
    db = get_db()
    db.execute(
        'UPDATE users SET cashBalance = cashBalance + ? WHERE userID = ?',
        (amount, userID,)
    )
    db.commit()