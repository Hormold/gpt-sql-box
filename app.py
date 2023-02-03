"""Web app to generate SQL queries from user input using GPT-3"""
import os
import json
import sys
import time
import psycopg2
import openai
from dotenv import load_dotenv
from flask import Flask, request, render_template
from schema import Schema

app = Flask(__name__, template_folder='tpl')
# Read .env file
load_dotenv()
TEMPLATE_DIR = os.path.abspath('./tpl')
APP_PORT = os.getenv('APP_PORT') or 5000
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('Please set DATABASE_URL in .env file.')
    sys.exit(1)
openai.api_key = os.getenv('OPENAI_TOKEN')
if not os.getenv('OPENAI_TOKEN'):
    print('Please set OPENAI_TOKEN in .env file.')
    sys.exit(1)

# Generate SQL Schema from PostgreSQL
schema = Schema()
sql_schema, json_data = schema.index()
print('SQL data was generated successfully.')

@app.get('/')
def index():
    """Show SQL Schema + prompt to ask GPT-3 to generate SQL queries"""
    # Get JSON data (not escaped)
    normalized_json_data = json.dumps(json_data);
    return render_template(
        'index.html',
        prompt=prompt,
        sql_schema=sql_schema,
        json_data=normalized_json_data
    )

@app.post('/generate')
def generate():
    """Generate SQL query from prompt + user input"""
    try:
        content = request.json
        print('Content:', content)
        user_input = content['query']
        query_temperture = content['temp']
        selected = content['selected']
        print('Selected tables:', selected)
        print('User input:', user_input)
        print('Query temperture:', query_temperture)

        # Update prompt
        regen_schema = schema.regen(selected)
        new_prompt = f'Given an input question, respond with syntactically correct PostgreSQL. Be creative but the SQL must be correct, not nessesary to use all tables. {regen_schema}'
        print('New prompt:', new_prompt)
    

        # Generate SQL query from prompt + user input
        final_prompt = f'{new_prompt}\n\nInstructions: {user_input}\n\nSQL:\n'

        # Ask GPT-3
        gpt_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=final_prompt,
            temperature=float(query_temperture),
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n"]
        )

        # Get SQL query
        sql_query = gpt_response['choices'][0]['text']
        print('Generated SQL query:', sql_query)

        # Return json
        return {
            'success': True,
            'sql_query': sql_query
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'sql_query': err
        }

@app.post('/run')
def execute():
    """Execute SQL query and show results in a table"""
    # Get SQL query
    try:
        ts_start = time.time()
        content = request.json
        sql_query = content['query']
        print('Run SQL query:', sql_query)

        # Execute SQL query and show results in a table
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(sql_query)
        results = cur.fetchall()

        # Return json with all columns names and results
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in results]
        seconds_elapsed = time.time() - ts_start
        return {
            'success': True,
            'columns': columns,
            'results': results,
            'seconds_elapsed': seconds_elapsed
        }
    except psycopg2.Error as err:
        print(err)
        return {
            'success': False,
            'error': err
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': err
        }


# Run web app
if __name__ == '__main__':
    app.run(debug=True, port=int(APP_PORT))
