#BigBucks Project_Team_18
- Team Members: Luke, Shiv, Darshan, and Abraham


To Run Application (fresh start), in terminal:
1. In config.py, insert Alpha Advantage API Key
2. flask --app bigbucks init-db
3. flask --app bigbucks run --debug

To Run Application, in terminal:
1. flask --app bigbucks run --debug

To get admin role:
1. In CLI, cd into database directory
2. Run this command:
    sqlite3 stock_database.db
3. Run this command:
    UPDATE Users SET role = 'admin' WHERE userID = '<target_user_ID>';

To use stock search tool, in URL bar, enter "http://127.0.0.1:5000/stock_search". 

Make sure no database currently exists in instance folder. 
If so, delete database and start with step one again <--Should not happen anymore, remove?

To run VM (VM shuts down at 6 am every morning, if you can't login text Abraham to turn VM on)
1. run ssh YOURNETID@vcm-39911.vm.duke.edu
2. Enter netid password
3. Sudo to serviceuser to run anything

To actually run vm:
1. systemctl enable stock.service
2. systemctl start stock.service

Flask description for VM is Stock Service, can be changed if nessecary. 
