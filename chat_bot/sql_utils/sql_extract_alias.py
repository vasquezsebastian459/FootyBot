import sqlparse
from sqlparse.sql import Identifier, Function, IdentifierList
from sqlparse.tokens import Whitespace


# This script is used to extract the alias name, function name, and column name from a SQL query.
# THis is the format of the output from the script:
# [{'alias_name': 'total_saves', 'function': 'count', 'column_name': 'save_id'}]

def is_function(token_part):
    """Parse a string and check if it represents a SQL function."""
    parsed = sqlparse.parse(token_part)[0]  # Parse the string into tokens
    for token in parsed.tokens:
        if isinstance(token, Function):
            return True  # Return True if any of the tokens is a Function
    return False

def extract_alias_and_column_from_identifier(token):
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
            if is_function(function_part):
                # Extract the function name and column name from the function part.
                function_name, column_name = extract_function_and_column(function_part)
            else:
                # If the token is not a function, treat the entire token as a column name.
                function_name = None
                column_name = function_part
            return alias.strip(), function_name, column_name.strip()
    return None, None, None

def extract_function_and_column(function_part):
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

def get_alias(query):
    aliases = []
    parsed = sqlparse.parse(query)[0]
    for token in parsed.tokens:
        
        if isinstance(token, Identifier):
            alias, function_name, column_name = extract_alias_and_column_from_identifier(token)
            if alias:
                output = {'alias_name': alias, 'function': function_name, 'column_name': column_name}
                aliases.append(output)
                return aliases
        elif isinstance(token, IdentifierList):
            for identifier in token.get_identifiers():
                
                alias, function_name, column_name = extract_alias_and_column_from_identifier(identifier)
                if alias:
                    output = {'alias_name': alias, 'function': function_name, 'column_name': column_name}
                    aliases.append(output)
                    return aliases
    return None


# Example usage
# sql_query = "SELECT player_id, COUNT(save_id) AS total_saves FROM public.t_save"

# sql_query = "SELECT COUNT(save_id) FROM public.t_save"
# sql_query = "SELECT save_id AS total_saves FROM public.t_save" 
# sql_query = "SELECT save_id AS total_saves , save_ids as tttFROM public.t_save" 
# sql_query = "SELECT player_id, COUNT(save_id) AS total_saves FROM public.t_save WHERE match_id IN (SELECT match_id FROM public.t_match WHERE season_id = 816527) GROUP BY player_id ORDER BY total_saves DESC LIMIT 1"
# print(sql_query)
# parsed = sqlparse.parse(sql_query)[0]

# output_alias = get_alias(sql_query)
# print(output_alias)
