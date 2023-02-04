"""Generate SQL Schema from PostgreSQL"""
import os
import sys
from dotenv import load_dotenv
import psycopg2

# Read .env file
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

class Schema:
    """Generate SQL Schema from PostgreSQL"""

    def __init__(self, schema = 'public'):
        """Connect to PostgreSQL database"""
        self.schema = schema
        try:
            self.conn = psycopg2.connect(DATABASE_URL)
        except psycopg2.OperationalError as err:
            print(f'Unable to connect!\n{err}')
            sys.exit(1)
        else:
            print('Connected to PostgreSQL database successfully.')
        self.cur = self.conn.cursor()
        self.comments = []
        self.tables = []
        self.columns = []

    def get_tables(self):
        """Get list of tables"""
        self.cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (self.schema,))
        tables = self.cur.fetchall()
        self.tables = tables
        return tables

    def get_all_comments(self):
        """Get list of all comments"""
        self.cur.execute('select c.table_schema, c.table_name,  c.column_name, pgd.description from pg_catalog.pg_statio_all_tables as st inner join pg_catalog.pg_description pgd on (pgd.objoid = st.relid) inner join information_schema.columns c on (pgd.objsubid   = c.ordinal_position and c.table_schema = st.schemaname and c.table_name   = st.relname);')
        comments = self.cur.fetchall()
        self.comments = comments
        return comments

    def get_columns(self, table):
        """Get list of columns for a table"""
        # Get column names, types and comments if available
        self.cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = %s AND table_name = %s", (self.schema, table))
        columns = self.cur.fetchall()
        return columns

    def regen(self, selected):
        """Regenerate SQL Schema only for selected tables"""
        if len(selected) == 0:
            return 'No tables selected.'
        prompt = ''
        tables = self.tables
        comments = self.comments
        for table in tables:
            if table[0] in selected:
                columns = self.get_columns(table[0])
                prompt += f'The "{table[0]}" table has columns: '
                for column in columns:
                    cmnt = ''
                    for comment in comments:
                        if comment[0] == self.schema and comment[1] == table[0] and comment[2] == column[0]:
                            cmnt = comment[3]
                            break
                    if cmnt == '':
                        prompt += f'{column[0]} ({column[1]}), '
                    else:
                        prompt += f'{column[0]} ({column[1]} - {cmnt}), '
                prompt = prompt[:-2] + '. '
        return prompt

    def index(self):
        """Generate SQL Schema"""
        prompt = ''
        json_data = {}
        tables = self.get_tables()
        comments = self.get_all_comments()
        for table in tables:
            columns = self.get_columns(table[0])
            prompt += f'The "{table[0]}" table has columns: '
            json_data[table[0]] = []
            for column in columns:
                cmnt = ''
                for comment in comments:
                    if comment[0] == self.schema and comment[1] == table[0] and comment[2] == column[0]:
                        cmnt = comment[3]
                        break
                if cmnt == '':
                    prompt += f'{column[0]} ({column[1]}), '
                else:
                    prompt += f'{column[0]} ({column[1]} - {cmnt}), '
                json_data[table[0]].append({
                    'name': column[0],
                    'type': column[1],
                    'comment': cmnt,
                    "seleted": True
                })
            prompt = prompt[:-2] + '. '
        return prompt, json_data
