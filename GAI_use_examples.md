# Generative AI Tool Use Examples
### Example #1
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We were looking for some guidance on how to make our system modular by separating different elements into different files, functions, and definitions
3. The prompt you presented to your tool:
“For an application that allows users to buy and sell stocks, view their portfolio, assess their holdings, and manage their account, what are some examples of ways to modularize the code to reduce unnecessary dependencies and make the code more manageable?
4. A description of how you applied the tool’s output:
ChatGPT provided some potential options for separating different files within our system, such as having a python file for buy/sell functionality, one for portfolio functionality, one for external API calls, one for account management, etc. We took this into account when creating multiple files for different parts of the BigBucks system.
5. Your assessment of how the tool helped:
In this case, the tool was helpful because it helped us develop an approach for how to best structure the code for our application in different files. This helped us make our system modular and facilitate easy changes without damaging other parts of the system.



### Example #2
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We were seeking advice on how to design an intuitive user interface that would be easy to navigate for our users
3. The prompt you presented to your tool:
What are some best practices for designing an intuitive and user-friendly interface for a web app where users can buy and sell stocks?
4. A description of how you applied the tool’s output:
One key insight we got from ChatGPT was to separate our website into multiple different pages, then to have a navigation bar at the top where users can easily move between pages. We applied this insight and added a navigation bar for easy access to different functionalities.
5. Your assessment of how the tool helped:
The tool helped us in designing our user interface, because we had considered the option of putting many functionalities on one main home page, but realized it may be better to allow simple navigation between many pages that focus on one functionality.



### Example #3
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We wanted to make sure we handled a variety of user inputs during the buying and selling of stocks, and were prepared to handle bad input
3. The prompt you presented to your tool:
What kinds of bad user input should we be checking for on a web app where users are buying and selling stocks by entering tickers and quantities?
4. A description of how you applied the tool’s output:
ChatGPT  gave us a list of checks we should consider, like making sure the quantity of stock purchased is positive, making sure they have enough balance to make the purchase, and ensuring that the ticker exists.
5. Your assessment of how the tool helped:
This information was helpful, because it led to us inserting additional constraints that ensured the quantity was positive, and they were entering valid tickers that represent real stocks.



### Example #4
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We noticed that some pages in our system had long loading times, so we wanted to know some ways we could reduce that
3. The prompt you presented to your tool:
What are some common causes for slow performance loading pages on a website, and what are ways to fix or address those issues?
4. A description of how you applied the tool’s output:
After reading through the ChatGPT response, we found that the problem we were dealing with was related to making extensive API calls upon loading a page, rather than getting data from the database. Using this information, we changed some functionalities to store data in the database earlier, then fetch from the database when a page needs to be loaded.
5. Your assessment of how the tool helped:
ChatGPT’s response was very helpful, because it gave us a list of possible causes for slow loading speed, and we then went back to our system and checked to see which was the culprit.



### Example #5
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We were running into a problem where our user login only worked on one person’s computer and not another, and we could not figure out why
3. The prompt you presented to your tool:
We have a web application where I can log in on my computer, but a friend is unable to log in on his computer. What could be some potential causes for this issue and how can we solve it?
4. A description of how you applied the tool’s output:
One key suggestion from ChatGPT was to try using the same login information vs different login information on the two computers. Once we realized that one login was working and one wasn’t, we were able to recognize that the issue was related to our database constraints relating to integers and text input.
5. Your assessment of how the tool helped:
In this case, ChatGPT was helpful because it helped us identify the root cause of a problem we were facing, and gave us a series of trial-and-error options to experiment with. Once we found the cause of the problem, implementing the solution was simple.



### Example #6
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We wanted to determine the best way to structure the architecture of our system so that it was efficient in handling requests and throwing errors. 
3. The prompt you presented to your tool:
Given the following goals for our application:(inserted our goals), how should I best structure the architecture of my application to efficiently handle the many requirements without duplicating code or efforts. 
4. A description of how you applied the tool’s output:
The tool gave a good outline on how the product architecture, especially the trading implementation, should be set up and we could all work forward through that with a clear outline in mind. 
5. Your assessment of how the tool helped:
I thought it helped a lot because it gave a definitive and understandable answer on the high level structure of our product and ways to better approach it. 



### Example #7
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
While making our wireframe diagram we wanted to know the best ways to implement the principles shown in class. 
3. The prompt you presented to your tool:
Given the following principles, what are the best ways to implement them to increase effectiveness of their attributes?
4. A description of how you applied the tool’s output:
The tool provided an in depth analysis of how each principle could be implemented in many different ways and the effectiveness of each option. We considered all these before moving forward with our sketches and were able to build out prototypes around these concepts. 
5. Your assessment of how the tool helped:
The tool helped quite a bit actually, it was useful to see applied ideas of the principles shown in class and think about them from a new angle of how they can be used in multiple ways. 



### Example #8
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
While creating our “definition of done”, we were not entirely sure what all that should include, and since it was a large part of our code reviews we wanted to make sure everyone was on the same page. 
3. The prompt you presented to your tool:
We are creating a stock trading application project and are working on a “definition of done” that everyone should adhere to when pushing code to the repo for finished issues, what are the most important concepts our definition of done should enforce. 
4. A description of how you applied the tool’s output:
We used the outline the AI gave us to adjust and tweak our definition of done to make it most effective for our team. 
5. Your assessment of how the tool helped:
The AI tool wasn’t as helpful in this situation, it really just returned information that we were already aware of and had written down. 



### Example #9
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
We were fetching data from our database and trying to display it on the page, but we couldn’t figure out how to get the data into the right format, since it was a Sqlite3 row, and we needed it in string or dictionary format
3. The prompt you presented to your tool:
How to convert sqlite3 row data to dictionary or strings so it can be displayed on html page
4. A description of how you applied the tool’s output:
The tool suggested an iterative approach of going through each sqlite3 row, getting the necessary information, and adding it to a dictionary that can be passed to the front-end, so we implemented this strategy
5. Your assessment of how the tool helped:
The tool was helpful because it gave us a step-by-step approach of one way to convert sqlite3 row data to a dictionary, and made it easy for us to learn and use this approach



### Example #10
1. Name of the tool you used:
ChatGPT
2. A description of the problem or question you were seeking to solve:
Before attempting to convert the 510 Efficient Frontier code from C++ to Python, we wanted to know if there were any key factors to keep in mind, such as differences in functionality or implementations between the two languages
3. The prompt you presented to your tool:
When converting code from C++ to Python that involves many numeric variables and matrix calculations, what are some key things to keep in mind?
4. A description of how you applied the tool’s output:
The tool provided some key insights about monitoring data types, ensuring matrix operations operate in the same manner, and checking for loss of data during calculations, which we made sure to implement when developing the efficient frontier in python.
5. Your assessment of how the tool helped:
In this case, ChatGPT was very helpful because it gave us a list of things to monitor and look out for as we worked on converting code to python, which saved us some time and prevented potential errors that we could have run into.



