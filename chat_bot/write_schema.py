from run_query import get_db_data
import os
from psycopg2 import sql
import psycopg2



db_password = os.getenv('DB_PASSWORD', 'default_value')
# Database connection parameters
db_params = {
    'dbname': 'madridlabs',
    'user': 'api',
    'password': db_password,
    'host': 'db.driblab.com',
    'port': '5432',
} 

# Connect to the PostgreSQL database
conn = psycopg2.connect(**db_params)
cur = conn.cursor()

# SQL query to retrieve schema information

# this query is to get the data from the nnormal tables

query = """
    SELECT table_schema, table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    AND table_schema NOT LIKE 'pg_toast%'
    ORDER BY table_schema, table_name, ordinal_position;
"""
#This query is to get the data from the materizalied views
query_vm = """
SELECT 
    nsp.nspname AS table_schema,
    cls.relname AS table_name,
    att.attname AS column_name,
    typ.typname AS data_type
FROM 
    pg_catalog.pg_attribute att
JOIN 
    pg_catalog.pg_class cls ON att.attrelid = cls.oid
JOIN 
    pg_catalog.pg_type typ ON att.atttypid = typ.oid
JOIN 
    pg_catalog.pg_namespace nsp ON cls.relnamespace = nsp.oid
WHERE 
    cls.relkind = 'm'  -- 'm' stands for materialized view
    AND att.attnum > 0
    AND NOT att.attisdropped
    AND nsp.nspname NOT IN ('pg_catalog', 'information_schema')  -- Exclude system schemas
    AND nsp.nspname NOT LIKE 'pg_toast%'
ORDER BY 
    nsp.nspname, cls.relname, att.attnum;
"""
cur.execute(query_vm)

# Fetch the result
schema_info = cur.fetchall()

# Close the cursor and connection
cur.close()
conn.close()

# Now write the schema information to a markdown file
with open('chat_bot/vm_materialized_views/vm_database_schema.md', 'w') as f:
    current_table = ""
    for row in schema_info:
        table_schema, table_name, column_name, data_type = row
        # Check if we are at a new table
        if current_table != f"{table_schema}.{table_name}":
            current_table = f"{table_schema}.{table_name}"
            f.write(f"\n## Table `{current_table}`\n")
            f.write("| Column Name | Data Type |\n")
            f.write("| ------------ | ---------- |\n")
        # Write the column information
        f.write(f"| {column_name} | {data_type} |\n")

print("Schema written to 'database_schema.md'")


# Calculate the number of tokens in the schema file
def calculate_tokens(file_path):
    with open(file_path, 'r') as f:
        text = f.read()
        tokens = text.split()
        return len(tokens)

file_path = 'chat_bot/vm_materialized_views/vm_database_schema.md'
number_of_tokens = calculate_tokens(file_path)
print(f"Estimated number of tokens: {number_of_tokens}")


# file_path = './chat_bot/schema.txt'
# number_of_tokens = calculate_tokens(file_path)
# print(f"Estimated number of tokens: {number_of_tokens}")
