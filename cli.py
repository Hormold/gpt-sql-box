"""CLI for GPT-3 SQL query generator."""
import sys
import os
import openai
from schema import Schema
from dotenv import load_dotenv

load_dotenv()
if not os.getenv('OPENAI_TOKEN'):
    print('Please set OPENAI_TOKEN in .env file')
    sys.exit(1)

if __name__ == '__main__':
    openai.api_key = os.getenv('OPENAI_TOKEN')
    schema = Schema()
    sql_schema, _ = schema.index()
    sql_schema = schema.regen(['users']) # Remove this line to generate schema for all tables

    query_temperture = 0.5
    prompt = input('Enter prompt to generate SQL query: ')
    final_prompt = f'Given an input question, respond with syntactically correct PostgreSQL. Be creative but the SQL must be correct, not nessesary to use all tables.\n\n{sql_schema}\n\nInstructions: {prompt}\n\nSQL:\n'

    gpt_response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=final_prompt,
        temperature=float(query_temperture),
        max_tokens=200,
        stop=["\n\n"]
    )

    print(f'GPT-3 response:\n\n{gpt_response["choices"][0]["text"]}')
