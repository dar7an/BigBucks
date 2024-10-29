# BigBucks

BigBucks is a stock trading simulation application. It allows users to simulate buying and selling stocks with virtual money. The application uses real-time stock data from the AlphaVantage API.

### Prerequisites

- Python 3.x
- Flask
- SQLite
- requests
- pytest
- Werkzeug
- numpy
- pandas
- click

### Running the Application

1. Clone the repository

2. Enter in terminal: pip install -r requirements.txt

3. In bigbucks/config.py, insert Alpha Advantage API Key using the following format:

API_KEY = "YOUR_KEY_HERE"

4. If database instance DOES NOT EXIST YET (meaning no .db file exists in bigbucks/database directory), enter this in the terminal:

flask --app bigbucks init-db

Note: if database errors occur, delete existing .db file and run initialization command again

5. Enter in terminal: flask --app bigbucks run --debug

#### Using the application as a "user"

1. Register an account
2. Log in to that account

#### Using the application as an "admin":

To get admin role:

1. Navigate to the database directory in your terminal

2. Run the following commands:

sqlite3 stock_database.db

UPDATE Users SET role = 'admin' WHERE userID = '<target_user_ID>';
