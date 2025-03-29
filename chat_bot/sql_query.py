import sqlparse
import sqlparse.tokens
from sqlparse.tokens import Keyword, DML, Wildcard, Token, Name, Whitespace, Punctuation
from sqlparse.sql import IdentifierList, Identifier, Function, Parenthesis, Where, Comparison,TokenList, Token
import re
from sql_extract_alias import get_alias
from print_colors import print_colored, print_colored_full_line
import json
import logging
from logger_manager import LoggerManager
from run_query import get_db_data, init_connection_pool,close_connection_pool

# Define a sql query class
class Query:
    def __init__(self, id, cleaned_query, schema, logger):
        self.id = id
        self.query = cleaned_query
        self.parsed = self.parse_query() # Parse the SQL query
        self.schema = schema # The schema used to validate the query
        self.logger = logger
        self.valid = None
        self.enhanced_query = None
        
        self.table = None
        self.columns = None
        self.alias = None

        self.tokens = self.get_sql_tokens()
        self.select_columns = self.get_select_columns()

        self.correct_table_name() # First we correct the table name. Some tables need the pro. prefix

        self.enhance_query() # We enhance the query by adding ids, where clauses and making columns Not Null



    
    def display_query(self):
        print_colored_full_line(f"Query ID: {self.id}", "WHITE")
        print(f"Generated Query: {self.query}")


    def parse_query(self):
        # Parse the SQL query
        parsed = sqlparse.parse(self.query)
        if parsed:
            return parsed[0]
        return None
    def check_retrieval_query(self):
        """
        This funciton checks if the query is only a retrieval query
        If the query is attempting to INSERT, UPDATE, DELETE, or CREATE or anything else it will return False
        Checks if any of the tokens are a DML statement other than SELECT
        """ 
        
        for token in self.parsed.tokens:
            if token.ttype is sqlparse.tokens.DML and token.value.upper() not in ['SELECT']:
                self.retrival = False
                return False , 'Invalid SQL: The query is not a SELECT statement.'
        self.retrival = True
        return True , 'The query is a SELECT statement.'
    
    def is_function(self, token_part):
        """Parse a string and check if it represents a SQL function."""
        parsed = sqlparse.parse(token_part)[0]  # Parse the string into tokens
        for token in parsed.tokens:
            if isinstance(token, Function):
                return True  # Return True if any of the tokens is a Function
        return False

    def extract_alias_and_column_from_identifier(self, token):
        """
        Extracts the alias and column used within a token that may encapsulate a function as an identifier.
        Specifically handles tokens like 'COUNT(save_id) AS total_saves' where the entire token may be treated as an Identifier.
        """
        if isinstance(token, Identifier):
            # Convert the token to string directly to handle alias and function.
            token_content = str(token).lower()
            if ' as ' in token_content:
                # Split by ' AS ' to separate function and alias.
                function_part, alias = token_content.split(' as ')           
                if self.is_function(function_part):
                    # Extract the function name and column name from the function part.
                    function_name, column_name = self.extract_function_and_column(function_part)
                else:
                    # If the token is not a function, treat the entire token as a column name.
                    function_name = None
                    column_name = function_part
                return alias.strip(), function_name, column_name.strip()
        return None, None, None

    def extract_function_and_column(self, function_part):
        """
        Extracts the function name and the column used from a string that represents a function call.
        """
        # Strip any wrapping whitespace and parentheses.
        function_part = function_part.strip()
        # Find the first opening parenthesis to separate the function name from its arguments.
        function_name = function_part[:function_part.find('(')]
        # Extract the argument inside the parentheses.
        column_name = function_part[function_part.find('(') + 1:function_part.rfind(')')]
        return function_name, column_name
    
    def check_wildcard(self):
        

        select_seen = from_seen = False
        wildcard_present = None

        for token in self.parsed.tokens:
            if token.ttype is DML and token.value.upper() == 'SELECT':
                select_seen = True
            elif select_seen and not from_seen and token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
            elif select_seen and not from_seen:
                if isinstance(token, Function):
                    # Allow function calls like COUNT(*)
                    for child_token in token.tokens:
                        if child_token.ttype == Wildcard:
                            wildcard_present = False # Allow this usage of wildcard
                elif isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        if identifier.ttype == Wildcard:
                            wildcard_present =  True  # Reject usage of wildcard in SELECT * FROM table
                elif isinstance(token, Identifier):
                    if token.ttype == Wildcard:
                        wildcard_present =  True  # Reject usage of wildcard in SELECT * FROM table
                elif token.ttype == Wildcard:
                    wildcard_present =  True  # Reject usage of wildcard in SELECT * FROM table
        
        if wildcard_present:
            return False, 'The query contains a wildcard "*"!'
        
        return True , 'The query does not contain a wildcard "*"'
    def get_alias(self):
        aliases = []
        parsed = sqlparse.parse(self.query)[0]
        for token in parsed.tokens:
            
            if isinstance(token, Identifier):
                # print()
                # print(token)
                # print()
                alias, function_name, column_name = self.extract_alias_and_column_from_identifier(token)
                if alias:
                    output = {'alias_name': alias, 'function': function_name, 'column_name': column_name}
                    aliases.append(output)
                    return aliases
            elif isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    
                    alias, function_name, column_name = self.extract_alias_and_column_from_identifier(identifier)
                    if alias:
                        output = {'alias_name': alias, 'function': function_name, 'column_name': column_name}
                        aliases.append(output)
                        return aliases
        return None


    def handle_function(self,token):
        column = None
        func_name = None
        
        # Iterate through the sub-tokens of the function token
        for sub_token in token.tokens:
            
            if isinstance(sub_token, Parenthesis):
                # Handle the tokens inside the parentheses
                for sub_sub_token in sub_token.tokens:
                    
                    if isinstance(sub_sub_token, Identifier):
                        column = sub_sub_token.get_name()
                    
                    elif sub_sub_token.ttype == Wildcard:  # Handle wildcard
                        column = '*'

            elif sub_token.ttype is Keyword or sub_token.ttype is None:
                
                if func_name is None:  # Only set func_name if it's not already set
                    func_name = sub_token.value.upper()

        return column , {func_name:column}
        
    
    def get_sql_tokens(self):


        # Extract SELECT and FROM tokens
        select_seen = from_seen = False
        columns = []
        functions =[]
        aliases = []
        
        table = None

        for token in self.parsed.tokens:
            # print_colored(f"Token: {token} - Type {token.ttype}", "RED")
            if token.ttype is DML and token.value.upper() == 'SELECT':
                select_seen = True
            elif select_seen and not from_seen and token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
            elif select_seen and not from_seen:
                #print_colored(f"- Token: {token} - Type {token.ttype}", "GREEN")
                if isinstance(token, IdentifierList):
                    #print_colored(f"-- Token: {token} - Type IdentifierList", "YELLOW")
                    for identifier in token.get_identifiers():
                        if identifier.ttype is Keyword:  # This is for the specific case when a column is named the same as a SQL KEYWORD for example position
                            # append the keyword as a column name
                            
                            columns.append(identifier.value)
                        elif identifier.ttype == Wildcard:  # Handle wildcard
                            columns.append('*')
                        elif isinstance(identifier, Function):
        
                            column , func_dict = self.handle_function(identifier)
                            columns.append(column)
                            functions.append(func_dict)
                        else:
                            
                            alias, func, column = self.extract_alias_and_column_from_identifier(identifier)
                            if alias and column and func:
                                columns.append(column)
                                functions.append({func: column})
                                aliases.append({'alias_name': alias, 'function': func, 'column_name': column})
                            else:
                                columns.append(identifier.get_name())
                elif isinstance(token, Identifier):
                    #print_colored(f"-- Token: {token} - Type Identifier", "BLUE")
                    if token.ttype == Wildcard:  # Handle wildcard
                        columns.append('*')
                    else:
                        columns.append(token.get_name())  # get name is for the alias name and get_real_name is for the column name of the alias
                elif isinstance(token, Function):
                    #print_colored(f"-- Token: {token} - Type Function", "CYAN")
                    #print_colored(token,"RED")
                    column , func_dict = self.handle_function(token) # This return a dict like this: {'function': func_name, 'column': column}
                    columns.append(column)
                    functions.append(func_dict)
                    
                elif token.ttype == Wildcard:  # Handle wildcard directly
                    #print_colored(f"-- Token: {token} - Type Wildcard", "RED")
                    columns.append('*')

                elif isinstance(token, Where): # Handle WHERE clause
                    # Iterate through the tokens in the WHERE clause
                    for where_token in token.tokens:
                        if isinstance(where_token, Comparison):
                            # Split the comparison token to get the column identifier
                            for sub_token in where_token.tokens:
                                if isinstance(sub_token, Identifier):
                                    #print_colored(f"-- WHERE Token: {sub_token} - Type sub_token", "ORANGE")
                                    columns.append(sub_token.get_real_name())
                                elif sub_token.ttype is Name:
                                    #print_colored(f"-- WHERE Token: {sub_token} - Type sub_token", "ORANGE")
                                    columns.append(sub_token.value)
                        elif isinstance(where_token, Identifier):
                            #print_colored(f"-- WHERE Token: {where_token} - Type Identifier", "ORANGE")
                            columns.append(where_token.get_real_name())
                            

                else:
                    x = token
                    #print_colored(f"-- Token: {token} - Type OTHER", "MAGENTA")
            elif from_seen and isinstance(token, Identifier):
                
                table = token.get_name()
                from_seen = False
                # break

        # Use the filter function to remove None values
        columns = list(filter(None, columns))

        self.columns = columns
        self.table = table

        # Get Aliases if present in the query:
        # aliases = self.get_alias()
        # Return the extracted tokens
        self.alias = aliases

        tokens = {'table': table, 'columns': columns, 'functions' : functions, 'alias': aliases}
        return tokens


    def get_select_columns(self):
        select_columns = []
        select_from_part = self.query[self.query.lower().index('select')+6:self.query.lower().index('from')].strip()


        for column in self.columns:
            if column in select_from_part:
                select_columns.append(column)

        select_columns = list(set(select_columns))
        return select_columns


    def validate_alias(self):
        """
        This function should only be run if there are aliases in the query.
        """
        Valid_alias = True
        message = ""
    
        for alias in self.alias:
            if alias['column_name'] not in self.schema[self.table]:
                message = f"Invalid SQL: The column '{alias['column_name']}' is not in the table '{self.table}'."
                Valid_alias = False
                return [Valid_alias, message]
            else:
                alias_name = alias['alias_name']
                message = f"The SQL Alias is correct regarding table '{self.table}', column name '{alias['column_name']}' with alias_name '{alias_name}'."
                
                return [Valid_alias, message]

    def check_columns(self):
        """
        This funcitons checks if the columns in the query are in the table's columns from the schema
        """
        # Validate columns against schema
        table_columns = self.schema.get(self.table, [])
        invalid_columns = [col for col in self.columns if col not in table_columns and col != '*']

        # Attempt to resolve invalid columns using aliases
        if invalid_columns:
            for alias in self.alias:
                alias_col_name = alias.get('alias_name')
                if alias_col_name in invalid_columns:
                    invalid_columns.remove(alias_col_name)
                    
                    print_colored(f"REMOVED INVALID COLUMN: {alias_col_name}", "RED")
        print_colored(invalid_columns, "BLUE")


        if invalid_columns:
            message = "Invalid SQL: The following columns are not in the table's schema: " + ', '.join(invalid_columns)
            return False, message
        else:
            
            return True , "Columns are valid"
        
    def check_table(self):
        """
        This function checks if the table in the query is in the schema
        """
        if self.table not in self.schema:
            self.valid = False
            message = f"Invalid SQL: The table '{self.table}' is not in the schema."
            return False , message
        else:
            
            return True , 'Table is in schema'
        
    def check_alias(self):

        alias = self.alias
        if alias:
            # self.validate_alias()

            print(self.tokens)

    def run_checks_query(self):
        """
        This function runs all the checks for the query
        """
        try:

            checks = [
                self.check_columns,
                self.check_table,
                self.check_retrieval_query,
                self.check_wildcard
            ]
            validity_counter = 0
            len_checks = len(checks)

            error_messages = []
            self.error_message = None
            for check in checks:
                validity, message = check()
                if validity:
                    validity_counter += 1
                    
                else:
                    error_messages.append(message)

            test_record = f"Number of checks passed: {validity_counter} \nNumber of checks failed: {len_checks - validity_counter} \nTotal checks: {len_checks}"
            self.test_record = test_record
            if len_checks == validity_counter:
                self.valid = True
            else:
                self.valid = False
                self.error_message = error_messages
                for error in error_messages:
                    print(f"Error: {error}")

        except Exception as e:
            print(f"Error: {e}")
            self.valid = None

    def test_query_db(self):
        """
        This function tests the query in the database
        """
        init_connection_pool()

        data = get_db_data(self.query,self.logger)
        close_connection_pool()
        if data[0] == 'Database error':
            print_colored("Failed query", "RED")
            return False, data[2]

        else:
            print_colored("Sucessful query", "GREEN")
            columns , rows = data
            # Calculate the shape
            num_columns = len(columns)
            num_rows = len(rows)
            shape = (num_rows, num_columns)
            print(f"Data Shape: {shape} ")
            return True , shape
        
    def add_ids_to_query(self, query , schema):
        sql_tokens =  self.tokens # this extracts the table and columns from the sql query

        query_columns = sql_tokens['columns'] # This are the columns selected in the query
        query_columns = self.select_columns

        table = sql_tokens['table'] # Get the table used in the query
        table = self.table

        columns = schema[table] # Get all the columns of the table in the schema file
        schema_columns = self.schema[table] # Get all the columns of the table in the schema file
        
        # Define a list of aggregate functions
        aggregate_functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP_CONCAT", "STRING_AGG"]
        
        # Regex to detect if any aggregate function is used
        aggregate_regex = r"\b(" + "|".join(aggregate_functions) + r")\b"
        # Check if the query contains any aggregate functions
        if re.search(aggregate_regex, query, re.IGNORECASE):
            print("Query contains aggregate functions.")
            return self.query  # Return the original query
        
        # Get columns to add from the schema dictionary
        table_schema = {table: schema_columns}
        
        # Id columns to look for
        id_columns = ['player_id', 'team_id', 'match_id', 'season_id'] 

        # Get Ids columns relevant to the table used in the query
        id_columns = [col for col in table_schema[table] if col in id_columns] # Id columns inside the table used in the query
        
        # Discard Id columns that have already been selected
        id_columns = [col for col in id_columns if col not in query_columns] # This will be the ids columns that were missing from the query

        if id_columns:
        # Find the current SELECT clause and capture it
            select_clause_search = re.search(r"SELECT (.*?) FROM", query, re.IGNORECASE)
            
            if select_clause_search:
                # Extract the current SELECT clause
                current_columns = select_clause_search.group(1).strip()
                
                
                # Prepare new SELECT clause with additional ID columns
                if current_columns != '*':  # Check if current selection is not a wildcard
                    new_columns = ', '.join([current_columns] + id_columns)
                    new_select_clause = f"SELECT {new_columns}"
                    
                    # Replace the original SELECT clause with the new one
                    modified_query = re.sub(r"SELECT .*? FROM", f"{new_select_clause} FROM", query, 1, re.IGNORECASE)

                    return modified_query
                else:
                    print_colored_full_line(f"SELECT CLAUSE IS A WILDCARD: {query}", "RED")
                    return query
            else:
                print_colored_full_line(f"SELECT CLAUSE NOT FOUND IN QUERY: {query}", "RED")
                return query
        else:
            print("No suitable '_id' columns found in the schema.")
            return query

    def correct_table_name(self):
    
        """
        This function corrects the table names in the query
        """
        correct_table_names = {
            'vm_det_player_placer': 'pro.vm_det_player_placer', 
            'vm_det_player_gbe': 'pro.vm_det_player_gbe',
            'vm_agg_season_player_all' : 'pro.vm_agg_season_player_all',
            'vm_agg_season_player_all' : 'pro.vm_agg_season_player_all',
            'vm_fac_games_player' : 'pro.vm_fac_games_player',
            
        }
        
        if self.table in correct_table_names.keys():

            self.query = self.query.replace(self.table, correct_table_names[self.table])
            
            return self.query
            
    
    def exclude_plyr_tms_ids(self):
        self.parsed = self.parse_query()

        # This function add the conditions below into the query. So that it doesnt return players like: Best Midfielder
            # Exclude player_ids like 'Best' and 'Top'
        exclude_player_ids =  [60, 61, 62, 63, 64, 65, 66, 80 , 81, 82 , 83, 84 , 85, 86, 100, 101 , 102, 103, 104, 105, 106, 110, 111, 112, 113, 114,115 ,116]
        exclude_player_ids = [str(player_id) for player_id in exclude_player_ids]
        exclude_player_ids_str = ", ".join(exclude_player_ids)
        exclude_player_ids_condition = f" player_id not in ({exclude_player_ids_str})"

        #player_id_condition = "player_id not in (60, 61, 62, 63, 64, 65, 66, 100)"
        team_id_condition = "team_id not in (21, 22, 23, 24, 25, 66, 97, 98, 99)"

        
        where_clause_found = False
        selecting_player_id = 'player_id' in self.columns
        selecting_team_id = 'team_id' in self.columns

        insert_index = None

        # Iterate over tokens to modify or add WHERE clause
        for i, token in enumerate(self.parsed.tokens):
            if isinstance(token, Where):
                where_clause_found = True
                new_conditions = []
                if selecting_player_id:
                    new_conditions.append(exclude_player_ids_condition)
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
                conditions.append(exclude_player_ids_condition)
            if selecting_team_id:
                conditions.append(team_id_condition)

            condition_str = ' WHERE ' + ' AND '.join(conditions)
            where_tokens = [
                sqlparse.sql.Token(Whitespace, ' '),
                sqlparse.sql.Token(Keyword, condition_str)
            ]
            
            # Insert or append new WHERE clause
            if insert_index is not None:
                self.parsed.tokens.insert(insert_index, TokenList(where_tokens))
            else:
                self.parsed.tokens.extend(TokenList(where_tokens))

        self.query = str(self.parsed)

    def find_earliest_clause(parsed_tokens, clauses):
        """Helper function to find the earliest occurrence of specified clauses."""
        positions = (next((i for i, token in enumerate(parsed_tokens)
                        if token.ttype is Keyword and token.value.upper() in clauses), None) for clause in clauses)
        # Filter out None and return the smallest index
        positions = [pos for pos in positions if pos is not None]
        return min(positions) if positions else len(parsed_tokens)
    
    def add_is_not_null_clauses(self):
        """
        Modifies an SQL query to add IS NOT NULL clauses for relevant columns not ending in '_id' or '_name'.
        """
        # parsed = sqlparse.parse(query)[0]
        # parsed = self.parsed

        # Filter columns that don't end with '_id' or '_name'
        relevant_columns = [col for col in self.select_columns if not (col.endswith("_id") or col.endswith("_name"))]
        
        # Filter columns that don't end with '_id' or '_name' and are not equal to '*'
        relevant_columns = [col for col in self.select_columns if not (col.endswith("_id") or col.endswith("_name")) and col != '*']

        if len(relevant_columns) == 0:
            return self.query
        
        # Decide between logical operator 'AND' or 'OR' based on the number of relevant columns
        logical_operator = ' OR ' if len(relevant_columns) > 1 else 'AND'
        
        # Generate IS NOT NULL conditions for relevant columns
        is_not_null_conditions = [f"{col} IS NOT NULL" for col in relevant_columns]

        # Create a single string from conditions, properly joined by ' AND ' or ' OR '
        conditions_str = logical_operator.join(is_not_null_conditions)


        where_clause_found = False
        for token in self.parsed.tokens:
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
            insert_index = self.find_earliest_clause(self.parsed.tokens, clauses)

            # Create and insert a new WHERE clause
            where_clause = TokenList([
                Token(Whitespace, ' '),
                Token(Keyword, 'WHERE '),
                Token(Whitespace, ' '),
                Token(Keyword, conditions_str)
            ])
            self.parsed.tokens.insert(insert_index, where_clause)

        # Return the modified query as a string
        self.query = str(self.parsed)
        

    def enhance_query(self):
        """
        This function enhances the query by adding the ids, where clauses and making columns Not Null.
        """
        if self.valid:
            # Remove the ";" at the end of the query
            self.query = self.query.replace(';', '')

            # We add relevant ids to the query
            self.query = self.add_ids_to_query(self.query,self.schema)

            # If we are selecting player_id or team_id. We add a where clause to exclude some ids
            self.exclude_plyr_tms_ids()

            # we add an is not null clause to the query for columns that are not ids
            self.add_is_not_null_clauses()

            self.enhanced_query = self.query

        


    def run_query(self):
        """
        This function runs the query in the database. 
        The query should be enhanced and validated before running it.
        """
        self.run_sucessful = None
        self.running_error_message = None

        if not self.enhanced_query:
            self.enhanced_query = self.query

        self.sql_data = get_db_data(self.enhanced_query,self.logger)
        if self.sql_data [0] == 'Database error' or len(self.sql_data ) >= 3:
            # all sql data should be length 2. So any length greater than 2 means there was an error
            print_colored("Failed query", "RED")
            self.run_sucessful = False
            self.running_error_message = self.sql_data[2]
            
        
        else:
            print_colored("Sucessful query", "GREEN")
            self.run_sucessful = True


        if not self.run_sucessful:
            print(self.running_error_message)
            self.enhanced_query = self.running_error_message


        query_dict = {
                "name": f'SQL Data {self.id}',
                "query": self.enhanced_query,
                "sql_data": self.sql_data,
                'run_sucessful': self.run_sucessful,
                "query_perf_data": {}
            }

        return query_dict


        


if __name__ == "__main__":
    
    init_connection_pool()
    # The schema used to feed the validate_sql_query function
    # This one is different than the one used to extract the top n tables 
    with open('/Users/sebastianvasquez/BBA_Chatbot/chat_bot/schemas/merged_table2col.json', 'r') as file:
        schema = json.load(file)

    logger = LoggerManager.get_logger("SQL_Query_test").get_logger()
    
    logger.info("Starting SQL Query Validation Test")
    log_file_name = LoggerManager.get_log_file_name("SQL_Query_test")
    print(f"Log file for SQL_Query_test: {log_file_name}")


    query = f"SELECT * from t_player Limit 10"
    query = Query(1, query, schema, logger)
    query_dict = query.run_query()
    print(query_dict)

    exit()


    queries = [
        "SELECT player_id, team_id, index_score FROM vm_det_player_placer WHERE team_id = 4263 ORDER BY index_score DESC LIMIT 1;",
        "SELECT player_name, position, height, age, score_this_year, mins_played_this_year, mins_perc_this_year FROM vm_agg_year_player_loan WHERE team_name = 'Celta de Vigo' AND regular_season_id = 816527 AND position = 'FW' ORDER BY score_this_year DESC LIMIT 1;",
        "SELECT player_id, team_id, match_id, mins_played_team, mins_played, positions_played  FROM public.vm_fac_games_player  WHERE player_id = 1169575 AND season_id = 816527;",
        "SELECT player_id, team_id, xg, xa, individual_pressure, ball_progression, turnovers FROM public.vt_game_metric_player WHERE season_id = 816527 AND team_id != 4263 ORDER BY dl_index DESC LIMIT 1;",
        "SELECT player_name, team_name FROM vm_fac_player_search_lm WHERE team_name = 'Celta de Vigo' AND regular_season_id = 816527 AND player_id NOT IN (1683147, 1163536) ORDER BY random() LIMIT 1;"
    ]

    # for i, query in enumerate(queries):
    #     query = Query(i, query, schema, logger)
    #     query.run_checks_query()
    #     print(query.valid)
    #     print(query.enhanced_query)

    #     query_dict = query.run_query()
        

    #     print(query.run_sucessful)
    #     print_colored(query_dict, "ORANGE")


    query = "SELECT assists, goals FROM public.agg_season_player_pd WHERE player_id = 1598188 AND season_id = 816527 "
    #query = "SELECT Count(*) FROM public.agg_season_player_pd WHERE player_id = 1598188 AND season_id = 816527 AND assists IS NOT NULL"
    #query = "SELECT player_id, player_name, dribbles_won_90, age, height FROM vm_agg_season_player_similarity WHERE season_id = 816527"
    query = "SELECT assists, player_id, team_id, season_id, player_id, team_id, season_id FROM vm_agg_season_player_opta WHERE player_name = 'Artem Dovbyk' AND team_name = 'Girona FC' AND season_id = 816527;"
    query = "SELECT player_name, goals, player_id, season_id, team_id, player_id, season_id, team_id FROM vm_agg_season_player_info WHERE season_id = 816527   AND (goals IS NOT NULL)   AND (goals IS NOT NULL) ORDER BY goals DESC LIMIT 1"
    query = "SELECT AVG(goals_scored) FROM (SELECT COUNT(DISTINCT goal_id) AS goals_scored FROM public.t_goal WHERE player_id = 69936 AND match_id IN (SELECT match_id FROM t_match WHERE season_id = 816527) GROUP BY match_id) AS goals_per_match;"
    query = Query(3, query, schema, logger)

    query.run_checks_query()
    print(query.valid)
    print(query.enhanced_query)

    query_dict = query.run_query()
    

    print(query.run_sucessful)

    
    
    print_colored(query_dict, "ORANGE")
    close_connection_pool()
    exit()

    

    
    queries = ["SELECT Count(*), Count(player_id), player_id, player_name, dl_index FROM vm_agg_season_player_info WHERE team_id = 20076 AND season_id = 816527 ORDER BY dl_index DESC LIMIT 3",  "SELECT player_id, player_name, dl_index FROM vm_agg_season_player_similarity WHERE team_id = 20076 AND season_id = 816527 ORDER BY dl_index DESC LIMIT 3", "SELECT player_id, score_pd_float FROM public.agg_season_player_pd WHERE team_id = 20076 AND season_id = 816527 ORDER BY score_pd_float DESC LIMIT 3",  "SELECT player_id, player_name, dl_index FROM vm_agg_season_player_opta WHERE team_id = 20076 AND season_id = 816527 ORDER BY dl_index DESC LIMIT 3", "SELECT player_id, COUNT(DISTINCT match_id) FROM public.t_goal WHERE team_id = 20076 AND season_id = 816527 GROUP BY player_id ORDER BY COUNT(DISTINCT match_id) DESC LIMIT 3" ]

    # queries = ["Select Count(player_id), player from vm_agg_season_player_info"]
    # Generated alias for mock. First one is correct second is not
    # queries = ["SELECT p.player_id AS pid, p.player_name AS pname, p.team_id AS tid, p.team_name AS tname, p.games AS g, p.minutes_played AS mp, p.goals_90 AS g90, p.assists_90 AS a90 FROM public.vm_agg_season_player_similarity AS p WHERE p.season_id = 2023 ORDER BY p.goals_90 DESC", "SELECT player_id AS pid, player_name AS pname, teamid AS tid, team_name AS tname, games AS g, minutes_played AS mp, goals_per_90 AS g90, assists_per_90 AS a90 FROM public.vm_agg_season_player_similarity p WHERE p.seasonid = 2023 ORDER BY goals_per_90 DESC"]

    queries = [
        "SELECT player_id, team_id, season_id FROM public.agg_season_player_pd WHERE season_id = 816527 AND player_id IN (     SELECT player_id     FROM t_player     WHERE age < 25     AND height > 180     AND player_id IN (         SELECT player_id         FROM public.agg_season_player_pd         WHERE games_played_65mins >= 20         AND mins_played >= 2000         AND score",
        "SELECT player_id, player_name, team_id, season_id, age, height, games, minutes_played, dl_index, tackles_90 FROM vm_agg_season_player_similarity WHERE age < 25 AND height > 180 AND team_id IN (SELECT team_id FROM t_team WHERE country_id = 1 AND league_id = 1) AND games >= 20 AND minutes_played >= 2000 AND dl_index < 50 AND position = 'DL",
        "SELECT player_id, player_name, height, age, games_played, minutes_played, market_value, dl_index, player_position, player_secondary_position, team_name, league_name FROM vm_agg_season_player_info WHERE age < 25 AND height > 180 AND player_country_name = 'Spain' AND games_played >= 20 AND minutes_played >= 2000 AND market_value < 50000000 AND dl_foot = 'left' AND league_name = 'La Liga",
        "SELECT player_id, player_name, age, height, games_played, mins_played, market_value, player_position, percent_tackles, dl_index FROM vm_agg_season_player_opta WHERE age < 25 AND height > 180 AND country_id = 1 AND games_played >= 20 AND mins_played >= 2000 AND market_value < 50000000 AND dl_foot = 'Left' AND league_id = 1 ",
        "SELECT player_id, player_name, age, team_id, season_id, mins_played, games_lost FROM vm_agg_season_player_all WHERE age < 25 AND player_country_code = 'ESP' AND team_games_played >= 20 AND team_mins_played >= 2000 AND market_value < 50 AND height > 180 AND league_type_id = 1 AND position = 'DL' AND season_id = 816527 ORDER BY games_lost ASC LIMIT 1;"
    ]

    queries = [
        "SELECT player_id, player_name, goals_90 FROM vm_agg_season_player_similarity WHERE season_id = 816527 AND age < 25 AND team_id = 4265 ORDER BY goals_90 DESC LIMIT 5",
        "SELECT player_id, team_id, season_id, player_name, age, mins_played FROM vm_agg_season_player_all WHERE season_id = 816527 AND player_id IN (SELECT player_id FROM vm_agg_season_player_all WHERE season_id = 816527 AND age < 25 ORDER BY mins_played DESC LIMIT 5)",
        "SELECT player_id, player_name, goals FROM vm_agg_season_player_opta WHERE season_id = 816527 AND goals > 0 AND age < 25 ORDER BY goals DESC LIMIT 5",
        "SELECT player_id, COUNT(goal_id) as goals_scored FROM public.t_goal WHERE player_id IN (SELECT player_id FROM t_player WHERE age < 25) AND match_id IN (SELECT match_id FROM t_match WHERE season_id = 816527) GROUP BY player_id ORDER BY goals_scored DESC LIMIT 5",
        "SELECT player_id, SUM(score_pd) AS total_goals FROM public.agg_season_player_pd WHERE season_id = 816527 AND player_id IN (SELECT player_id FROM public.agg_season_player_pd WHERE season_id = 816527 AND age < 25) GROUP BY player_id ORDER BY total_goals DESC LIMIT 5"
    ]
    queries = [
        "SELECT player_id, season_id, SUM(dl_index) AS total_score FROM vm_agg_season_player_similarity WHERE season_id IN (816527, 816019, 815453, 814198, 813658) GROUP BY player_id, season_id ORDER BY total_score DESC LIMIT 1",
        "SELECT player_id, season_id, season_year FROM vm_agg_season_player_all WHERE season_id = 816527 ORDER BY team_games_played DESC LIMIT 1",
        "SELECT player_id, player_name, goals, season_id FROM vm_agg_season_player_info WHERE season_id in (816527, 816019, 815453, 814198, 813658) AND league_country_name = 'Spain' AND player_position IN ('FW', 'AML', 'AMR', 'FWL', 'FWR') ORDER BY goals DESC",
        "SELECT player_id, COUNT(*) as goals FROM public.t_goal WHERE season_id = 816527 GROUP BY player_id ORDER BY goals DESC LIMIT 1",
        "SELECT player_id, goals, season_id FROM vm_agg_season_player_opta WHERE season_id IN (816527, 816019, 815453, 814198, 813658) AND goals IS NOT NULL ORDER BY goals DESC LIMIT 1"
    ]

    queries = [
        "SELECT player_id, season_id, SUM(goals_scored) AS total_goals FROM vm_agg_season_player_all WHERE season_id IN (816527, 816019, 815453, 814198, 813658) AND league_type_id = 1 GROUP BY player_id, season_id ORDER BY total_goals DESC;",
        "SELECT player_id, season_id, SUM(dl_index) AS total_score FROM vm_agg_season_player_similarity WHERE season_id IN (816527, 816019, 815453, 814198, 813658) GROUP BY player_id, season_id ORDER BY total_score DESC;",
        "SELECT player_id, player_name, goals FROM vm_agg_season_player_info WHERE season_id = 816527 AND player_position IN ('FW', 'AML', 'AMR', 'FWL', 'FWR') ORDER BY goals DESC LIMIT 1;",
        "SELECT player_id, COUNT(goal_id) AS goals_scored FROM public.t_goal WHERE season_id = 816527 GROUP BY player_id ORDER BY goals_scored DESC LIMIT 1;",
        "SELECT player_id, player_name, goals, season_id FROM vm_agg_season_player_opta WHERE season_id IN (816527, 816019, 815453, 814198, 813658) AND league_country_name = 'Spain' AND player_position = 'FW' ORDER BY goals DESC;"
    ]


    # for idx, query in enumerate(queries):
    #     query = Query(idx, queries[idx], schema)
    #     query.display_query()
    #     print(query.tokens)
    #     query.run_checks_query()
    #     print(query.test_record)
    #     print_colored(f"QUERY VALID: {query.valid}", "GREEN")
    #     print()

    

    query = "SELECT player_id, player_name, goals, season_id, team_id FROM vm_agg_season_player_opta WHERE season_id IN (816527, 816019, 815453, 814198, 813658) AND league_country_name = 'Spain' AND player_position = 'FW'   AND player_id not in (60, 61, 62, 63, 64, 65, 66, 100) AND team_id not in (21, 22, 23, 24, 25, 66, 97, 98, 99)  AND (goals IS NOT NULL) ORDER BY goals DESC;"
    query = queries[3]
    query = "SELECT Count(*) FROM public.agg_season_team_info WHERE team_id = 4266 AND season_id = 816527"
    # query = "SELECT Count(*), player_id, player_name, dl_index FROM vm_agg_season_player_info WHERE team_id = 20076 AND season_id = 816527 ORDER BY dl_index DESC LIMIT 3",  "SELECT player_id, player_name, dl_index FROM vm_agg_season_player_similarity WHERE team_id = 20076 AND season_id = 816527 ORDER BY dl_index DESC LIMIT 3", "SELECT player_id, score_pd_float FROM public.agg_season_player_pd WHERE team_id = 20076 AND season_id = 816527 ORDER BY score_pd_float DESC LIMIT 3",  "SELECT player_id, player_name, dl_index FROM vm_agg_season_player_opta WHERE team_id = 20076 AND season_id = 816527 ORDER BY dl_index DESC LIMIT 3", "SELECT player_id, COUNT(DISTINCT match_id) FROM public.t_goal WHERE team_id = 20076 AND season_id = 816527 GROUP BY player_id ORDER BY COUNT(DISTINCT match_id) DESC LIMIT 3"
    #query = "SELECT COUNT(goal_id) AS goals_scored FROM public.t_goal WHERE match_id IN (SELECT match_id FROM public.t_match WHERE (home_team_id = 4265 AND away_team_id = 4279) OR (home_team_id = 4279 AND away_team_id = 4265))"

    query = Query(3, query, schema, logger)
    query.display_query()
    print(query.tokens)
    query.run_checks_query()
    print(query.test_record)
    print_colored(f"QUERY VALID: {query.valid}", "GREEN")
    print_colored(f"ERROR MESSAGE: {query.error_message}", "RED")

    #query.test_query_db()
    print()
    exit()

    

    init_connection_pool()

    query = "SELECT player_id, player_name, goals, season_id, team_id FROM vm_agg_season_player_opta WHERE season_id IN (816527, 816019, 815453, 814198, 813658) AND league_country_name = 'Spain' AND player_position = 'FW'   AND player_id not in (60, 61, 62, 63, 64, 65, 66, 100) AND team_id not in (21, 22, 23, 24, 25, 66, 97, 98, 99)  AND (goals IS NOT NULL) ORDER BY goals DESC;"

    data = get_db_data(query,logger)

    if data[0] == 'Database error':
        print_colored(f"Database error: {data[1]}", "RED")

    else:
        print_colored("Suceessful query", "GREEN")
        columns , rows = data
        # Calculate the shape
        num_columns = len(columns)
        num_rows = len(rows)
        print(f"Data Shape: \n- Col: {num_columns} \n- Rows:{num_rows}")


    close_connection_pool()

    exit()
    #query = "SELECT player_id, COUNT(goal_id)  FROM public.t_goal WHERE player_id IN (SELECT player_id FROM t_player WHERE age < 25) AND match_id IN (SELECT match_id FROM t_match WHERE season_id = 816527) GROUP BY player_id ORDER BY goals_scored DESC LIMIT 5"
    # print(extract_sql_tokens(query))

    
    query = Query(1, query, schema)

    query.display_query()
    print(query.tokens)
    query.run_checks_query()
    
    exit()
    print(query.check_wildcard())

    
    # print(query.has_wildcard())
    # x = query.check_retrieval_query()
    # print(x)
    

    
    
    




