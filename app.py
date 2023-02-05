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
OPENAI_ENGINE = os.getenv('OPENAI_ENGINE') or 'text-davinci-003'
TEMPLATE_DIR = os.path.abspath('./tpl')
PROMPT_DIR = os.path.abspath('./prompts')
APP_PORT = os.getenv('APP_PORT') or 5000
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('Please set DATABASE_URL in .env file.')
    sys.exit(1)

if os.getenv('OPENAI_TOKEN'):
    openai.api_key = os.getenv('OPENAI_TOKEN')

if not openai.api_key:
    print('Please set OPENAI_TOKEN in .env file or set token in UI') # Not a critical error

# Generate SQL Schema from PostgreSQL
schema = Schema()
sql_schema, json_data = schema.index()
print('SQL data was generated successfully.')

def load_prompt(name: str) -> str:
    """Load prompt from file"""
    with open(os.path.join(PROMPT_DIR, name + ".txt"), 'r', encoding='utf-8') as file:
        return file.read()

# Middleware to check key in request or in .env file
@app.before_request
def get_key():  
    """Get API key from request or .env file"""
    if (request.content_type != 'application/json'
        or request.method != 'POST'
        or request.path == '/run'):
        return
    content = request.json
    if not content['api_key'] and not openai.api_key:
        return {
            'success': False,
            'error': 'Please set OPENAI_TOKEN in .env file or set token in UI'
        }

    if content and content['api_key']:
        request.api_key = content['api_key']
    else:
        request.api_key = os.getenv('OPENAI_TOKEN')

@app.get('/')
def index():
    """Show SQL Schema + prompt to ask GPT-3 to generate SQL queries"""
    normalized_json_data = json.dumps(json_data)
    return render_template(
        'index.html',
        has_openai_key=bool(openai.api_key),
        sql_schema=sql_schema,
        json_data=normalized_json_data
    )

@app.post('/generate')
def generate():
    """Generate SQL query from prompt + user input"""
    try:
        content = request.json
        user_input = content['query']
        query_temperture = content['temp']
        selected = content['selected']
        print('Selected tables:', selected)
        print('User input:', user_input)
        print('Query temperture:', query_temperture)

        openai.api_key = request.api_key
        regen_schema = schema.regen(selected)
        fprompt = load_prompt('sql').replace('{regen_schema}', regen_schema).replace('{user_input}', user_input)
        # Edit prompt on the fly by editing prompts/sql.txt
        print(f'Final prompt: {fprompt}')

        # Ask GPT-3
        gpt_response = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=fprompt,
            temperature=float(query_temperture),
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n"]
        )

        used_tokens = gpt_response['usage']['total_tokens']

        # Get SQL query
        sql_query = gpt_response['choices'][0]['text']
        sql_query = sql_query.lstrip().rstrip()
        print('Generated SQL query:', sql_query)

        # Return json
        return {
            'success': True,
            'sql_query': sql_query,
            'used_tokens': used_tokens,
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
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
            'error': str(err)
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
        }

@app.post('/generate_prompt')
def generate_prompt():
    """Generate prompt from selected tables"""
    try:
        content = request.json
        selected = content['selected']
        query_temperture = content['temp']

        openai.api_key = request.api_key

        # Update prompt
        regen_schema = schema.regen(selected)
        final_prompt = load_prompt('idk').replace('{regen_schema}', regen_schema)
        print(f'Final prompt: {final_prompt}')

        gpt_response = openai.Completion.create(
            engine=OPENAI_ENGINE,
            prompt=final_prompt,
            temperature=float(query_temperture),
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n"]
        )

        used_tokens = gpt_response['usage']['total_tokens']

        # Get SQL query
        query = gpt_response['choices'][0]['text'].lstrip().rstrip()
        print('Generated prompt:', query)

        return {
            'success': True,
            'query': query,
            'used_tokens': used_tokens,
        }
    except Exception as err:
        print(err)
        return {
            'success': False,
            'error': str(err)
        }

@app.post('/generate_chart')
def generate_chart():
    """Generate chart from SQL query"""
    content = request.json
    csv_data = str(content['csv_data'])
    query_temperture = float(content['temp'])
    print('CSV data:', csv_data)
    print('Query temperture:', query_temperture)
    #chart_type = content['chart_type'] # bar, line, pie, scatter
    example_prompt = load_prompt('graph').replace('{csv_data}', csv_data)

    openai.api_key = request.api_key
    gpt_response = openai.Completion.create(
        engine=OPENAI_ENGINE,
        prompt=example_prompt,
        temperature=float(query_temperture),
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n\n"]
    )

    used_tokens = gpt_response['usage']['total_tokens']
    pseudo_code = gpt_response['choices'][0]['text'].lstrip().rstrip();
    chart_type = pseudo_code.split('|')[0]
    chart_data = pseudo_code.split('|')[1]

    return {
        'success': True,
        'chart_type': chart_type,
        'chart_data': chart_data,
        'used_tokens': used_tokens,
    }

# Run web app
if __name__ == '__main__':
    app.run(debug=True, port=int(APP_PORT))
