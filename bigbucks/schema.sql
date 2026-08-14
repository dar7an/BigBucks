PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS holdings;
DROP TABLE IF EXISTS historic_prices;
DROP TABLE IF EXISTS symbols;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    cash_balance REAL NOT NULL DEFAULT 1000000 CHECK (cash_balance >= 0),
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE holdings (
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (user_id, ticker),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 1),
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    total_price REAL NOT NULL CHECK (total_price > 0),
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE historic_prices (
    ticker TEXT NOT NULL,
    closing_date TEXT NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    adj_close_price REAL NOT NULL,
    volume INTEGER NOT NULL,
    PRIMARY KEY (ticker, closing_date)
);

CREATE TABLE symbols (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    exchange TEXT,
    overview_json TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_holdings_ticker ON holdings(ticker);
CREATE INDEX idx_tx_user_time ON transactions(user_id, created_at);
CREATE INDEX idx_tx_date ON transactions(created_at);
CREATE INDEX idx_prices_date ON historic_prices(closing_date);
