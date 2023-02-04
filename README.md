# GPT-3 SQL Query Generator and UI

This is simple python application to generate SQL Schema + prompt to ask GPT-3 to generate SQL queries.
It also has a simple UI to show results in a table.

**It can generate a prompt for you, if you don't know what to ask GPT-3.**

![](https://github.com/Hormold/gpt-sql-box/blob/master/docs/demo.gif?raw=true)


## How it works:
1. Getting SQL schemas from PostgreSQL and compile prompt from SQL Schema
3. Wait for user input
4. Generate SQL query from prompt + user input
5. Show SQL query and ask user to confirm or edit if it is correct before executing it
6. Execute SQL query and show results in a table

## Environment
- DATABASE_URL: PostgreSQL database URL
- OPENAI_TOKEN: OpenAI API token (Not nessessary, you can set it in the UI)
- APP_PORT: Port to run the application (default: 5000)

## How to run
1. It better to create a virtual environment using `python3 -m venv venv`
2. Install dependencies using `pip install -r requirements.txt`
3. Set environment variables in `.env` file in project root or in your system
4. Run the application using `python app.py` and open `http://localhost:5000` in your browser

## Contact 
If you have any questions, please contact me at [@define](https://t.me/define) in Telegram.