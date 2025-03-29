from run_query import get_db_data,init_connection_pool,close_connection_pool
from sql_query_validation import extract_sql_tokens
import sqlparse
from sqlparse.sql import Identifier, Where, TokenList,IdentifierList, Token
from sqlparse.tokens import Keyword, Whitespace, Punctuation
from print_colors import print_colored, print_colored_full_line
from config import client  # Import the client from the config module
from open_ai_messages.get_message import get_formatted_message # Import function from the get_message module
import json
import time
#This script is made to take an sql query and correct it by following some instructions

def openai_correct_query(query, instructions, temp = 0.2, max_tokens = 600):
    
    keyinfo = []
    
    # Extract the open ai prompt from  the JSON file at chat_bot/open_ai_messages/open_ai_messages.json
    message = get_formatted_message('openai_correct_query', [instructions])
    
    # Create a completion using the chat endpoint
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system",
            "content": message},
            {"role": "user",
            "content": query}
        ],
        temperature=temp , # Default is typically 1; lower temperature for more deterministic output
    )
    # Check if there is a valid response
    if completion.choices:
        choice = completion.choices[0]
        response = choice.message.content 
        print_colored_full_line(" ", "ORANGE")
        print_colored(f"openai_correct_query response: {response}", "ORANGE")
        print_colored_full_line(" ", "ORANGE")
        keyinfo.append(response)

        tokens_used = completion.usage.total_tokens
        rate_per_token = 0.5 / 1000000  # Price per token
        print(f"Total tokens used: {tokens_used}")
        print(f'Total tokens spent: {tokens_used*rate_per_token}')
        return keyinfo[0]
    else:
        print("No completion found.")

def correct_table_name(query,sql_tokens):
    correct_table_names = {
        'vm_det_player_placer': 'pro.vm_det_player_placer', 
        'vm_det_player_gbe': 'pro.vm_det_player_gbe',
        'vm_agg_season_player_all' : 'pro.vm_agg_season_player_all',
        'vm_agg_season_player_all' : 'pro.vm_agg_season_player_all'
    }
    table = sql_tokens['table']
    print(table)
    if table in correct_table_names.keys():
        query = query.replace(table, correct_table_names[table])
        return query
    else:
        return query
# query = 'SELECT gbe_score FROM vm_det_player_gbe WHERE player_id = 1598188 AND band_league = 2 AND pct_league_min = 100'
# sql_tokens = {'table': 'vm_det_player_gbe', 'columns': ['global_score'], 'alias': None}

# corrected_query = correct_table_name(query,sql_tokens)
# print(corrected_query)

def modify_sql_query(query, sql_tokens):
    
    # First we correct the table name
    # Sometables need the pro. prefix
    query = correct_table_name(query,sql_tokens)
    # This function add the conditions below into the query. So that it doesnt return players like: Best Midfielder
    player_id_condition = "player_id not in (60, 61, 62, 63, 64, 65, 66, 100)"
    team_id_condition = "team_id not in (21, 22, 23, 24, 25, 66, 97, 98, 99)"

    parsed = sqlparse.parse(query)[0]
    where_clause_found = False
    selecting_player_id = 'player_id' in sql_tokens['columns']
    selecting_team_id = 'team_id' in sql_tokens['columns']

    insert_index = None

    # Iterate over tokens to modify or add WHERE clause
    for i, token in enumerate(parsed.tokens):
        if isinstance(token, Where):
            where_clause_found = True
            new_conditions = []
            if selecting_player_id:
                new_conditions.append(player_id_condition)
            if selecting_team_id:
                new_conditions.append(team_id_condition)

            if new_conditions:
                condition_str = ' AND ' + ' AND '.join(new_conditions)
                token.tokens.append(sqlparse.sql.Token(Whitespace, ' '))
                token.tokens.append(sqlparse.sql.Token(Keyword, condition_str))

        elif token.ttype is Keyword and token.value.upper() in ['ORDER BY', 'GROUP BY', 'LIMIT']:
            insert_index = i
            break

    if not where_clause_found and (selecting_player_id or selecting_team_id):
        conditions = []
        if selecting_player_id:
            conditions.append(player_id_condition)
        if selecting_team_id:
            conditions.append(team_id_condition)

        condition_str = ' WHERE ' + ' AND '.join(conditions)
        where_tokens = [
            sqlparse.sql.Token(Whitespace, ' '),
            sqlparse.sql.Token(Keyword, condition_str)
        ]
        
        # Insert or append new WHERE clause
        if insert_index is not None:
            parsed.tokens.insert(insert_index, TokenList(where_tokens))
        else:
            parsed.tokens.extend(TokenList(where_tokens))

    return str(parsed)

def find_earliest_clause(parsed_tokens, clauses):
    """Helper function to find the earliest occurrence of specified clauses."""
    positions = (next((i for i, token in enumerate(parsed_tokens)
                    if token.ttype is Keyword and token.value.upper() in clauses), None) for clause in clauses)
    # Filter out None and return the smallest index
    positions = [pos for pos in positions if pos is not None]
    return min(positions) if positions else len(parsed_tokens)


def is_not_null_sql_query(query, sql_tokens):
    """Modifies an SQL query to add IS NOT NULL clauses for relevant columns not ending in '_id' or '_name'."""
    parsed = sqlparse.parse(query)[0]

    # Filter columns that don't end with '_id' or '_name'
    relevant_columns = [col for col in sql_tokens["columns"] if not (col.endswith("_id") or col.endswith("_name"))]
    
    # If there are no relevant columns, return the original query
    if len(relevant_columns) == 0:
        return query
    
    # Decide between logical operator 'AND' or 'OR' based on the number of relevant columns
    logical_operator = ' OR ' if len(relevant_columns) > 1 else 'AND'
    
    # Generate IS NOT NULL conditions for relevant columns
    is_not_null_conditions = [f"{col} IS NOT NULL" for col in relevant_columns]

    # Create a single string from conditions, properly joined by ' AND ' or ' OR '
    conditions_str = logical_operator.join(is_not_null_conditions)


    where_clause_found = False
    for token in parsed.tokens:
        if isinstance(token, Where):
            where_clause_found = True
            # Append ' AND ' followed by the conditions at the end of the WHERE clause
            token.tokens.append(Token(Whitespace, ' '))
            # token.tokens.append(Token(Punctuation, logical_operator))
            token.tokens.append(Token(Punctuation, ' AND '))
            # ADd opening parenthesis
            token.tokens.append(sqlparse.sql.Token(Punctuation, '('))
            token.tokens.append(Token(Keyword, conditions_str))
            
            # Add closing parenthesis
            token.tokens.append(sqlparse.sql.Token(Punctuation, ')'))
            token.tokens.append(Token(Whitespace, ' '))
            
            break

    if not where_clause_found and conditions_str:
        # If no WHERE clause found, insert one before ORDER BY, GROUP BY, or LIMIT
        clauses = ['ORDER BY', 'GROUP BY', 'LIMIT']
        insert_index = find_earliest_clause(parsed.tokens, clauses)

        # Create and insert a new WHERE clause
        where_clause = TokenList([
            Token(Whitespace, ' '),
            Token(Keyword, 'WHERE '),
            Token(Whitespace, ' '),
            Token(Keyword, conditions_str)
        ])
        parsed.tokens.insert(insert_index, where_clause)

    # Return the modified query as a string
    return str(parsed)
    
# # # Example usage

# Add complex queries here to test that all of them are handled correctly
test_queries = [
    "SELECT player_id, team_id, season_id, age FROM vm_agg_season_player_all ORDER BY age DESC LIMIT 10",
    "SELECT player_id, team_id, season_id, tackles_total FROM public.vt_season_stat_player WHERE season_id = 816527 ORDER BY tackles_total DESC LIMIT 10",
    "SELECT player_id, team_id, season_id, age, player_country_code  FROM vm_agg_season_player_all ORDER BY age DESC LIMIT 10",
    "SELECT player_name, goals, assists, yellow_cards, red_cards FROM vm_agg_year_player_info WHERE player_name = 'Lamine Yamal' AND year = 2023",
    "SELECT player_id, pct_int_game, current_band_league, last_band_league, band_league, gbe_score FROM vm_det_player_gbe WHERE player_id = 1598188 AND band_league IS NOT NULL"
    ]


### Get only 1 modified query ####

# query = 'SELECT player_id, pct_int_game, current_band_league, last_band_league, band_league, gbe_score FROM vm_det_player_gbe WHERE player_id = 1598188 AND band_league IS NOT NULL AND regular_season_id = 816527'
# modified_query = modify_sql_query(query,extract_sql_tokens(query) )
# modified_query = is_not_null_sql_query(modified_query,extract_sql_tokens(query))
# print(modified_query)

#### Get and RUN 1 modified query ####

# query = 'SELECT player_id, pct_int_game, current_band_league, last_band_league, band_league, gbe_score FROM vm_det_player_gbe WHERE player_id = 1598188 AND band_league IS NOT NULL'
# # query = test_queries[2]
# init_connection_pool()

# sql_tokens = extract_sql_tokens(query)    
# print(sql_tokens)

# modified_query = modify_sql_query(query,sql_tokens)
# corrected_query = is_not_null_sql_query(modified_query,sql_tokens)
# print(corrected_query)
# data = get_db_data(corrected_query)

# print(data)
# print_colored_full_line("\n", "GREEN")

# close_connection_pool()

#### TEST QUERIES ####

# print_colored_full_line("QUERY TEST", "RED")
# correct_queries = []
# init_connection_pool()
# for query in test_queries:
#     sql_tokens = extract_sql_tokens(query)    
#     print(sql_tokens)

#     modified_query = modify_sql_query(query,sql_tokens)
#     corrected_query = is_not_null_sql_query(modified_query,sql_tokens)
#     print(corrected_query)
#     data = get_db_data(corrected_query)
#     print(data)
#     if data[0] == "Database error":
#         correct_queries.append(False)
#     else:
#         correct_queries.append(True)
    
#     print_colored_full_line("\n", "GREEN")

# close_connection_pool()
# print()
# print_colored_full_line("QUERY TEST RESULTS", "RED")
# print_colored(f"Completed {sum(correct_queries)}/{len(correct_queries)} queries", "GREEN")



# queries_path = 'chat_bot/peformance/sql_query_list.json'

# with open(queries_path, 'r') as f:
#     queries = json.load(f)

# test_queries = queries[0:10]

# init_connection_pool()
# for query in test_queries:
#     print_colored_full_line("SQL Query Corrector", "GREEN")
    
#     print(query['query'])
#     print(query['data'])
#     print()
#     query = query['query']


    

#     sql_tokens = extract_sql_tokens(query)    

#     start_time = time.time()
#     modified_query = modify_sql_query(query,sql_tokens)
#     print(modified_query)
#     print(f"Total time taken: {time.time() - start_time}")
#     start_time = time.time()
#     corrected_query = openai_correct_query(query, message)
#     print(f"Total time taken: {time.time() - start_time}")

#     print(corrected_query)
    
#     data = get_db_data(modified_query)
    
#     print(data)
#     print_colored_full_line("\n", "GREEN")

# close_connection_pool()