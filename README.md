# BigBucks Project_Team_18
- Team Members: Luke, Shiv, Darshan, and Abraham

## Project Overview

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

### Virtual Machine (VM) Usage

To run the application on a VM, follow these steps:

1. SSH into the VM, using the following command:

ssh YOURNETID@vcm-39911.vm.duke.edu

2. Enter your NetID password 

3. Switch to the service user to run commands 

4. Enable and start the service, using the following commands:

systemctl enable stock.service

systemctl start stock.service

### Assignment Details

- all source code for the application exists in the bigbucks/ directory
- on the application, charts 14.1-14.4 can be found by searching a stock in the search tab
- charts 7.1-7.3 can be found by searching a stock on the search tab with "compare to SPY"
- our manual test cases can be found in the test_cases.md file (approved method by TA)
- for the Project Topic Assignment, we chose to document our product architecture (see Product Architecture/ directory) and document our GAI usage (see GAI_use_examples.md)
