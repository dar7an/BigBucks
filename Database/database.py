import sqlite3

# Define the database file name
db_file = "financial_database.db"

# Define SQL statements to create tables
create_users_table = """
CREATE TABLE Users (
    userID INTEGER PRIMARY KEY,
    firstName TEXT,
    lastName TEXT,
    email TEXT,
    password TEXT,
    cashBalance REAL,
    role TEXT
)
"""

create_portfolio_objects_table = """
CREATE TABLE PortfolioObjects (
    userID INTEGER,
    ticker TEXT,
    quantity INTEGER,
    PRIMARY KEY (userID, ticker),
    FOREIGN KEY (userID) REFERENCES Users(userID)
)
"""

create_transactions_table = """
CREATE TABLE Transactions (
    transactionID INTEGER PRIMARY KEY,
    userID INTEGER,
    ticker TEXT,
    amount REAL,
    unitPrice REAL,
    totalPrice REAL,
    orderType TEXT,
    dateTime TEXT,
    FOREIGN KEY (userID) REFERENCES Users(userID)
)
"""

create_historic_price_data_table = """
CREATE TABLE HistoricPriceData (
    ticker TEXT PRIMARY KEY,
    lastClosePrice REAL,
    date TEXT
)
"""

# Connect to the SQLite database
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# Create tables
cur.execute(create_users_table)
cur.execute(create_portfolio_objects_table)
cur.execute(create_transactions_table)
cur.execute(create_historic_price_data_table)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database created successfully.")
