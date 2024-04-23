# Test Cases

### Requirement 1

##### Test Case 1
- Input or Interaction: user registering with username = UserBob, first name = Bob, last name = Smith, email = bsmith@gmail.com, password = bsmithpass
- Expected Result: successful registered user and info added to database
- Outcome: Passed

##### Test Case 2
- Input or Interaction: user registering with username empty, first name = Joe, last name = Smith, email = fakeEmail, password = myPassword
- Expected Result: Registration not allowed due to invalid username and email
- Outcome: Passed

##### Test Case 3
- Input or Interaction: user above attempts to log in with username = UserBob, password = bsmithpass
- Expected Result: successful login to UserBob’s account
- Outcome: Passed

##### Test Case 4
- Input or Interaction: user attempts to log in with username = nonExistingUser, password = myPassword
- Expected Result: log-in fails due to no account with matching username/password
- Outcome: Passed


### Requirement 2

##### Test Case 5
- Input or Interaction: buy 100 shares of MSFT on 1/20/2021
- Expected Result: debit cash 22382.00, credit MSFT 22382.00
- Outcome: Passed

##### Test Case 6
- Input or Interaction: sell 100 shares of MSFT on 1/27/2021
- Expected Result: debit MSFT 23236.00, credit cash 23236.00
- Outcome: Passed

##### Test Case 7
- Input or Interaction: buy 10 shares of FAKETICKER on 4/1/2024
- Expected Result: no transaction allowed because of invalid ticker
- Outcome: Passed

##### Test Case 8
- Input or Interaction: buy 999999999 shares of MSFT on 4/1/2024
- Expected Result: no transaction allowed because of insufficient balance
- Outcome: Passed

##### Test Case 9
- Input or Interaction: sell 99999999 shares of AAPL on 4/1/24
- Expected Result: no transaction allowed because of insufficient stock
- Outcome: Passed


### Requirement 3

##### Test Case 10
- Input or Interaction: added AlphaVantage API key and tested company_overview endpoint
- Expected Result: receive json output from AlphaVantage API
- Outcome: Passed

##### Test Case 11
- Input or Interaction: pass AAPL ticker to store historical data for Apple stock
- Expected Result: 5+ years of historical AAPL price data stored in database
- Outcome: Passed

##### Test Case 12
- Input or Interaction: pass FAKETICKER to store historical price data
- Expected Result: no data storage occurs because of invalid ticker
- Outcome: Passed

##### Test Case 13
- Input or Interaction: fetch and store 5+ years of SPY index data
- Expected Result: 5+ years of SPY index data stored in database
- Outcome: Passed


### Requirement 4

##### Test Case 14
- Input or Interaction: add MSFT, AAPL, and GOOG to user portfolio and visit metrics page
- Expected Result: see efficient frontier calculation for MSFT, AAPL, and GOOG portfolio
- Outcome: Passed

##### Test Case 15
- Input or Interaction: add MSFT, AAPL, and GOOG to user portfolio and visit metrics page
- Expected Result: see Sharpe ratio calculation for MSFT, AAPL, and GOOG portfolio, using the US Treasury 10-year bond yield as the risk-free rate
- Outcome: Passed

##### Test Case 16
- Input or Interaction: create one user with AAPL and GOOG stock, and a second user with MSFT and T stock, then log-in to “admin” account
- Expected Result: display risk-return profile for the users specified and show total holdings
- Outcome: Passed

### Requirement 5

##### Test Case 17
- Input or Interaction: after adding multiple stocks(MSFT, AAPL, GOOG) to a portfolio, navigate to the portfolio/metrics page and view different reports
- Expected Result: on portfolio page we see list of stocks by ticker name, number of shares held and price in order
- Outcome: Passed

##### Test Case 18
- Input or Interaction: log in as admin and navigate to reports page after storing other data in database
- Expected Result: be able to see summary of all day’s market orders across all accounts in data base
- Outcome: Passed

### Requirement 6

##### Test Case 19
- Input or Interaction: User selects to view the price plot chart (Figure 14.1) for a selected stock(AAPL) in their portfolio.
- Expected Result: Display the price plot chart accurately showing the price movements of AAPL over a specified period.
- Outcome: Passed

##### Test Case 20
- Input or Interaction: User selects to view returns plot charts (Figures 14.2, 14.3, 14.4) for their portfolio.
- Expected Result: Display the three different returns plots showing daily, monthly, and annual returns of the selected stocks.
- Outcome: Passed

##### Test Case 21
- Input or Interaction: User opts to generate the stock price versus index price chart (Figure 7.1 of Balch) for a specific stock and index.
- Expected Result: Chart displays comparing the price movements of the selected stock with the chosen index(SPY). 
- Outcome: Passed

##### Test Case 22
- Input or Interaction: User requests the stock return versus index return time series chart (Figure 7.2 of Balch).
- Expected Result:Time series chart shows the returns of the stock compared to the index returns over the same period.
- Outcome: Passed

##### Test Case 23
- Input or Interaction: User selects to view the scatter plot of stock return versus index return (Figure 7.3 of Balch).
- Expected Result: Scatter plot accurately displays the correlation between stock returns and index returns.
- Outcome: Passed

### Requirement 9

##### Test Case 24
- Input or Interaction: Review of the final UI design to check the application of UX principles: figure-ground, similarity, proximity, common region, and continuity.
- Expected Result: The UI should clearly demonstrate the use of at least four UX principles as taught in class, enhancing usability and visual appeal.
- Outcome: Passed

##### Test Case 25
- Input or Interaction: User interaction with the newly implemented charting controls as per the updated design.
- Expected Result: All controls work as expected, allowing users to seamlessly navigate through different charting features without confusion or errors.
- Outcome: Passed

