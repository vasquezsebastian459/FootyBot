

import os
import re
import logging

import psycopg2
from psycopg2 import pool
from print_colors import print_colored,print_colored_full_line

import time
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


# Function to get the current time in a human-readable format
def get_readable_time():
    return datetime.fromtimestamp(time.time()).strftime('%m-%d %H:%M:%S')

# Global variable for connection pool
connection_pool = None

def init_connection_pool():
    global connection_pool
    db_params = {
        'dbname': 'madridlabs',
        'user': 'arrigo',
        'password': os.getenv('DRIBLAB_DB_PASSWORD'),
        'host': 'db.driblab.com',
        'port': '5432',
    }
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **db_params)
    # print_colored_full_line("", "CYAN")
    print_colored(f"Database connection pool initialized at: {get_readable_time()}", "CYAN")
    print_colored_full_line("", "CYAN")
    

def close_connection_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print_colored_full_line("", "CYAN")
        print_colored(f"Database connection pool closed at: {get_readable_time()}", "CYAN")
        print_colored_full_line("", "CYAN")
    else:
        print_colored("Connection pool was not initialized or already closed", "RED")
        print_colored_full_line("", "RED")
db_password = os.getenv('DB_PASSWORD', 'default_value')

# Database connection parameters
db_params = {
    'dbname': 'madridlabs',
    'user': 'api',
    'password': db_password,
    'host': 'db.driblab.com',
    'port': '5432',
} 

def extract_table(query):
    match = re.search(r'(FROM|JOIN)\s+([\w.]+)', query, re.IGNORECASE)

    if match:
        table_name = match.group(2)  # This is the second capture group, which should be the table name
        return table_name
    else:
        print("No table name found in the query")

# Function to remove a table by name
def remove_table(data, table_name):

    # BASE SCHEMA
    remaining_tables =[table for table in data if table['table_name'] != table_name] # REMEBER TO CHANGE TBL TO TABLE_NAME

    return remaining_tables

def get_db_data(query):
    # Connect to the database
    print_colored(f"Fetching data from the database at: {get_readable_time()} -> {query} ", "CYAN")
    conn = None
    try:
        conn = connection_pool.getconn()
        cur = conn.cursor()
        
        # Execute the SQL query
        cur.execute(query)
        
        # Fetch the results
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        
        # Prepare the result as a tuple of column names and rows
        result = (col_names, rows)

        # Close the cursor
        cur.close()

    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
        table = extract_table(query) # EVALUATE IF IT IS BETTER IF WE USE THE SQL TOKENS FUNCTION THAT IS THE SQL VALIDATION FILE.
        error = ['Database error', table, str(e)]
        return error

    except Exception as e:
        logging.error(f"Other error: {e}")
        return None

    finally:
        if conn is not None:
            connection_pool.putconn(conn)

    return result

# THIS WAS THE FUNCTION USED BEFORE THE CONNECTION POOL WAS IMPLEMENTED
def get_db_data2(query):
    # Connect to the database
    logging.debug("Connecting to the database")
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        # Execute the SQL query
        cur.execute(query)

        # Fetch and print the results
        rows = cur.fetchall()

        col_names = [desc[0] for desc in cur.description]
        # Prepare the result as a tuple of column names and rows
        result = (col_names, rows)

        # Close the cursor and connection
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        table = extract_table(query)
        error = ['Database error', table,str(e)]
        return error

    except Exception as e:
        print(f"Other error: {e}")
    finally:
        if conn is not None:
            conn.close()

    return result


if __name__ == "__main__":
    init_connection_pool()
    query = "SELECT * from t_player Limit 10"
    query = f"SELECT player_id, SUM(raw_score) AS total_score FROM public.vt_game_score_player WHERE season_id = 817531 AND player_id not in (60, 61, 62, 63, 64, 65, 66, 100) GROUP BY player_id ORDER BY total_score DESC LIMIT 1"
    data = get_db_data(query)
    print(data)
    close_connection_pool()

#query = "SELECT first_name, last_name, position, dob FROM public.t_player WHERE player_id = 1163220"
# query = "SELECT player_id, team_id, season_id, xA, xa_open_play, xa_set_piece FROM public.vt_season_metric_player WHERE season_id = 816527 AND xA IS NOT NULL AND xa_open_play IS NOT NULL AND xa_set_piece IS NOT NULL"
# data = get_db_data(query)
# print(data)