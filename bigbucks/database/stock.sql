CREATE TABLE Users (
    userID INTEGER PRIMARY KEY,
    firstName TEXT,
    lastName TEXT,
    email TEXT,
    password TEXT,
    cashBalance REAL,
    role TEXT
);

CREATE TABLE PortfolioObjects (
    userID INTEGER,
    ticker TEXT,
    quantity INTEGER,
    PRIMARY KEY (userID, ticker),
    FOREIGN KEY (userID) REFERENCES Users(userID)
);

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
);

CREATE TABLE HistoricPriceData (
   ticker            VARCHAR(5)    NOT NULL,  
   closing_date      DATE          NOT NULL,
   open_price        DECIMAL(16,6) NOT NULL,
   high_price        DECIMAL(16,6) NOT NULL,
   low_price         DECIMAL(16,6) NOT NULL,
   close_price       DECIMAL(16,6) NOT NULL,
   adj_close_price   DECIMAL(16,6) NOT NULL,
   volume            BIGINT        NOT NULL,
   PRIMARY KEY (ticker, closing_date)
);
