


from config import client  # Import the client from the config module
from open_ai_messages.get_message import get_formatted_message # Import function from the get_message module
import time
import traceback
from print_colors import print_colored, print_colored_full_line
import logging
from logger_manager import LoggerManager
import json
from Response import filter_response,print_colored_response, write_json
import ast
from run_query import init_connection_pool,close_connection_pool, get_db_data, print_table
from multiple_criteria_stats import add_stat_filters_to_query


# Helper function to get the data type
def get_data_type(column):
    data_types = {
    "integer" : ["age","height","games_played","minutes_played", "market_value"],
    "string" : ["tm_foot" , "position", "gbe_score", "side"],
    "date" : ['tm_end_contract_date', 'date_of_birth'],
    "bool" : ['national_team'],
    "list" : ['team_id', 'not_team_id', 'country_id', 'team_name', 'not_team_name', 'country_name']    
}
    for data_type, columns in data_types.items():
        if column in columns:
            return data_type
    return None

def map_name2id(column, name, entities_info):

    entity_id = None

    if column == "country_name":
        country_info = entities_info.get('country_info')
        if country_info:
            for country in country_info:
                country_name = country.get('country_name')
                
                if str(name.lower()) == str(country_name.lower()):
                    country_id = country.get('country_id')
                    if country_id:
                        entity_id = country_id

    if column in ['not_team_name', 'team_name']:
        team_info = entities_info.get('teams_info')
        if team_info:
            for team in team_info:
                team_name = team.get('info', {}).get('raw_name', 'None')
                if str(name.lower()) == str(team_name.lower()):
                    team_id = team.get('info').get('team_id')
                    entity_id = team_id
    return entity_id
    


def compile_criteria_info(criterias,entities_info):

    # Create a list to hold the result
    criteria_list = []

    # Special cases list // This are the cases where we need to map a name to an id
    special_cases = ['team_name', 'not_team_name', 'country_name']

    special_cases_name_map = {
        "team_name": "team_id",
        "not_team_name" : "not_team_id",
        "country_name" : "country_id"
    }

    # Iterate over the criteria and create the list of dictionaries
    for column, value in criterias.items():
        data_type = get_data_type(column)
        table = 'vm_agg_season_player_info'

        if column in special_cases:
            
            ids_list = []
            for name in value:
                entity_id = map_name2id(column, name, entities_info)
                ids_list.append(entity_id)

            column = special_cases_name_map.get(column)
            value = ids_list

        if column == 'date_of_birth':
            column = 'dob'

        if column == 'side':
            column = 'player_position_side'


        criteria_list.append({
            "column": column,
            "value": value,
            "data_type": data_type,
            "table": table
        })
    return criteria_list


def player_filter_criteria(response, temp = 0.3, max_tokens = 200): # This one is designed to handle the Raw Entities instead of Entities Info
    start_time = time.time()
    user_question = response.get('User Question')
    raw_entities = response.get('Raw Entities')
    session_id = response.get('Session Id')
    logger = LoggerManager.get_logger(f"user_{session_id}").get_logger()

    # Extract the open ai prompt from  the JSON file at chat_bot/open_ai_messages/open_ai_messages.json
    # message = get_formatted_message('question_classifier', [context])


    message = f"""
    You task is to analyze the question and identify by which criterias the user is asking for multiple criterias or filtering.
    Take into account the entities information to provide a response.
    {raw_entities}
    These are the categories for filtering/comparing players:

    Criteria / Values
    age / integer use < or > for less than or greater than, use this format: "< 25" or ">= 30". For ranges use "between 20 and 30"
    height / integer - in cms. For ranges use "between 170 and 180"
    date_of_birth / date type. Always in "year=month-day" format. Example: '1990-01-01'
    country_name / list - which refers to nationality of a player Example: ["Spain","England","France"]. If only one country is needed, use ["Spain"]
    games_played / integer "refers to the number of games played by a player in a season" should be with > or < or =. For ranges use "between 25 and 35"
    minutes_played / integer "refers to the number of minutes played by a player in a season". For ranges use "between 1500 and 3200"
    tm_end_contract_date / date type. Example: 2030-01-01 refers to the end date of the player's contract
    market_value / integer "refers to the market value of a player in thousands of euros". For ranges use "between 15000 and 3000"
    team_name / list - refers to a team filter where the player is playing. Example: ["Manchester United", "Chelsea"]. If only one team is needed, use ["Manchester United"]
    not_team_name / list - refers to a team filter where the player is not playing. Example: ["Juventus", "Parma"]. If only one team is needed, use ["Juventus"]
    tm_foot / 'right' or 'left' or 'both' refers to the strong foot of the player
    season_name / list - refers to the season filter where the player played. Example: ["La Liga", "Premier League"]. If only one season is needed, use ["La Liga"]
    position / string - refers to the position of the player
    side / string - refers to the side the player plays.
    national_team / bool - "True" or "False" refers if the player played in the national team
    gbe_score / string - refers to the Governing Body Endorsement score. Use "good" for scores above 15, "review" for scores between 10 and 15, and "bad" for scores under 10.
    you should respond in this format:

    {{
        "criterias": {{
            "criteria1": "value1",
            "criteria2": "value2",
            "criteria3": "value3"
        }},
        "statistics": {{
            'stat1': 'top', # range should be: top, bottom, average, "between x and y" or use integer with < or > for less than or greater than.
            'stat2': 'between 4 and 10',
            'stat3': 'average',
            'stat4': '> 5',
            'stat5': '< 10',
            'stat6': '>=20'
            }} 
    }}

    - Replace stat1, stat2, stat3 with the statistics the users asks want to filter by.

    Some common statistics: goals,dribbles,assist, crosses, expected_goals, 
    progressive_passes, progressive_carries, passes_completed, touches, tackles, interceptions, aerials_won, fouls_committed, fouls_drawn, shots

    anything related on how a player performs in a game add it to the statistics dictionary.

    An example:

    {{
        "criterias": {{
            "country_name": ["Spain"],
            "not_team_name": ["Real Madrid", "Barcelona"],
            "national_team": false,
            "market_value": "< 100000",
            "age": "< 20",
            "gbe_score": "good"
    }},
        "statistics": {{
            'passes': '>1000', 
            'crosses': 'between 20 and 50',
            'expected_goals': '>= 10'}} 
    }}

    if they arent any statistics to filter by, you can return the list as empty like this:
    
    {{
        "criterias": {{
            "country_name": ["Germany"],
            "not_team_name": ["Bayern Municj", "Juventus"],
            "national_team": false,
            "market_value": "< 100000",
            "age": "< 20",
            "gbe_score": "good"
    }},
        "statistics": {{
        "goals" : "> 20",
        "dribbles" : "top",
        "takles" : "between 40 and 100"
        }} #Empty list if no statistics mentioned
    }}

    * Make sure to add the futball statistics like dribbling,goalscoring and etc to the statistics dictionary
    * Also always add the "top", "bottom" or "average" to the statistics dictionary
    * When asking for a top N players, or best players in general. The statistic should be dl_index. 

    For example:
    - Give me the top 10 best players that have played in the premier league:
    "statistics": {{ 
        "dl_index": "top"
    }}

    Example of date criteria:
    "tm_end_contract_date": "< \"2027-01-01\"",
    "date_of_birth": "< \"1990-01-01\""
    

    Example of national_team:

    "give me a player that has not played for their national team", national_team = False
    "Only show me players that have played for their national team", national_team = True
    "Give me a player that is very fast, good at shooting and plays in la liga", national_team = [] # No national team was mentioned
    - If the question doesnt mention anything related to national team dont include it in the criteria dict

    Example of GBE score:
    "Give me a player with a good GBE score", gbe_score = "good"
    "Give me a player with a bad GBE score", gbe_score = "bad"
    "Give me a player with a review GBE score", gbe_score = "review"
    - if the question doesnt mention anything related to GBE score dont include it in the criteria dict
    Example: "Give me a player that has played in La liga and that is good at shooting and passing" -> "gbe_score" : [] # No GBE score was mentioned

    
    These are the possible sides in our database:
    - Left
    - Centre
    - Right
    - Left/Centre
    - Centre/Right
    - Left/Right
    - Left/Centre/Right
    Example of side:
    "Give me a player that plays on the right", "side" : "Right"
    "Give a player that plays both on the centre and right", "side" : "Centre/Right"

    
    
    Example of position:
    These are the possible football positions in our database:

	•	DC: Defender Center
	•	MC: Midfielder Center
	•	MR: Midfielder Right
	•	DMR: Defensive Midfielder Right
	•	FWL: Forward Left
	•	FWR: Forward Right
	•	DML: Defensive Midfielder Left
	•	DR: Defender Right
	•	AML: Attacking Midfielder Left
	•	Sub: Substitute
	•	ML: Midfielder Left
	•	DL: Defender Left
	•	DMC: Defensive Midfielder Center
	•	GK: Goalkeeper
	•	AMC: Attacking Midfielder Center
	•	AMR: Attacking Midfielder Right
	•	FW: Forward

    if the user asks for a player in a given position add it in the criteria dict
    Example: User: "Give me a goalkeeper that has played in the premier league" "position" : "GK"

    If the user doesnt mention a position dont include it in the criteria dict:
    Example: "Give me a player that has played in the premier league and is less than 25 years old" -> "position" : [] # No Position was mentioned


    Example of not_team_name:

    Question : give me a player that does not play in Real MAdrid or Barcelona 
    "not_team_name" : ["Real Madrid", "Barcelona"]

    Example of country_name:
    Question: Give me a player from Spain that has good dribbles per 90.
    "country_name": ["Spain"]
     Question: Give me a player from La Liga that has good dribbles per 90.
    "country_name": [] # None because the user didnt ask for a player from a specific country, he asked for a league/season


    Give me a player from La liga that has good shooting:
    "country_name": [] # None, this question doesnt ask the nationality of a player. It filters by league
    If a criteria is not present in the question dont include it in the dicionary.
    Only add country_name as a criteria if the user asks for a player from a specific country.

    Always use " " and not ' ' for the values in the dictionary.
    
    If a user asks for a player from a league/seasons that does not mean to add the country_name as a criteria.
    only add a criteria to the dictionary if the users specifically asks for it. IF not is ok to leave it blank.

    Dont write any comments in the output, only the JSON response.
    """
    
    # Create a completion using the chat endpoint
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system",
            "content": message},
            {"role": "user",
            "content":user_question}
        ],
        temperature=temp ,
        max_tokens = max_tokens# Default is typically 1; lower temperature for more deterministic output
    )

    # Check if there is a valid response
    if completion.choices:
        
        choice = completion.choices[0]
        generated_response = choice.message.content 
        
        logger.info(f"\nOPEN AI RESPONSE Criteria Classifier:\n{generated_response}")
        # Get Token Usage
        tokens_used = completion.usage.total_tokens
        
        cleaned_response = clean_openai_response(generated_response)
        logger.info(f"\CLEANED RESPONSE:\n{cleaned_response}")

        cleaned_response =  clean_and_update_criterias(cleaned_response)
        logger.info(f"\CLEANED RESPONSE2:\n{cleaned_response}")

        total_time = time.time() - start_time
        return cleaned_response, tokens_used , total_time
    else:
        print("No completion found.")

def clean_openai_response(response):
    try:
        # Correcting 'None' to 'None' to allow for proper JSON parsing
        response = response.replace('None', 'None')
        response = response.replace('True', 'true')
        response = response.replace('False', 'false')
        response = response.replace("'", '"')

        # Using json.loads() - This will work if the response is in correct JSON format
        cleaned_response = json.loads(response)
    
        return cleaned_response
    except json.JSONDecodeError as e:
        print("Error parsing the list using json.loads():", str(e))

def clean_and_update_criterias(cleaned_response):
    session_id = cleaned_response.get('Session Id')
    logger = LoggerManager.get_logger(f"user_{session_id}").get_logger()

    # Remove the keys that are not needed and that are empty
    keys2check = [
        'age', 'height', 'weight', 'country_id', 'games_played', 
        'minutes_played', 'tm_end_contract_date', 'market_value', 
        'team_id', 'not_team_id', 'tm_foot', 'position', 
        'team_name', 'not_team_name', 'country_name', 'side',
        'national_team', 'gbe_score', 'date_of_birth']
    

    criterias = cleaned_response.get("criterias")
    keys_to_remove = []
    misplaced_statistics = []

    for key, value in criterias.items():
        try:
                
            if key not in keys2check:
                if value in ['top','bottom','average']: # This means that the classifier added stats into the basic info criteria
                    misplaced_statistics.append({key : value})
                keys_to_remove.append(key)
            elif not value:
                if key == "national_team" and str(value).lower() in ['true', 'false']:
                    continue
                keys_to_remove.append(key)
        except Exception as e:
            # If there is an error just remove the key
            logger.error(f"Error cleaning key: {key} with value: {value}")
            keys_to_remove.append(key)

    # Remove the keys marked for removal
    for key in keys_to_remove:
        criterias.pop(key)

    if misplaced_statistics:
        stats = cleaned_response.get('statistics')
        if stats is None:
            cleaned_response['statistics'] = {} # Create the statistics dictionary if it does not exist

        misplaced_statistics_dict = { k:v for d in misplaced_statistics for k, v in d.items()}
        cleaned_response["statistics"].update(misplaced_statistics_dict)

    cleaned_response["criterias"] = criterias

    return cleaned_response

def build_date_condition(col_name, value):
    operations = ['<=', '>=', '=', '>', '<']

    condition = None

    if 'between' and 'and' in value.lower():
        start_date1 = value.find('between') + len('between')
        and_pos = value.find('and') 
        
        date1 = value[start_date1:and_pos].strip()

        date2 = value[and_pos+3:].strip()
        condition = f"{col_name} BETWEEN '{date1}' AND '{date2}'"

    else:
        for op in operations:
            if op in value:
                date = value.split(op)[1]
                date = date.strip()
                value = f"{op} '{date}'"
                
                condition = f"{col_name} {op} '{date}'"
                break # Break to avoid matching multiple operators

    return condition

def get_sides_condition(col_name, inputed_side):
    
    db_sides = [
        "Left",
        "Centre",
        "Right",
        "Left/Centre",
        "Centre/Right",
        "Left/Right",
        "Left/Centre/Right"
    ]

    # Split the input string and capitalize each component
    inputed_side_components = set(component.capitalize() for component in inputed_side.split('/'))
    sides_list = []

    for db_side in db_sides:
        db_sides_components = set(db_side.split('/'))
        if inputed_side_components.issubset(db_sides_components):
            sides_list.append(db_side)

    values_str = ", ".join(f"'{side}'" for side in sides_list)
    condition = f"{col_name} IN ({values_str})"
    return condition


def add_criterias2_query(compiled_criterias,season_ids_str):

    table_prefix = "vaspi."
    select_query = "SELECT vaspi.player_id, vaspi.player_name"
    from_query = "FROM vm_agg_season_player_info AS vaspi JOIN vm_agg_season_player_opta AS vaspo ON vaspo.player_id = vaspi.player_id "
    filter_query = f"WHERE vaspi.season_id IN ({season_ids_str}) AND vaspo.season_id IN ({season_ids_str})"

    # Exclude player_ids like 'Best' and 'Top'
    exclude_player_ids =  [60, 61, 62, 63, 64, 65, 66, 80 , 81, 82 , 83, 84 , 85, 86, 100, 101 , 102, 103, 104, 105, 106, 110, 111, 112, 113, 114,115 ,116]
    exclude_player_ids = [str(player_id) for player_id in exclude_player_ids]
    exclude_player_ids_str = ", ".join(exclude_player_ids)
    exclude_player_ids_condition = f" AND vaspi.player_id not in ({exclude_player_ids_str})"

    filter_query += exclude_player_ids_condition
    
    select_cols = []

    for criteria in compiled_criterias:
    
        d_type = criteria.get('data_type') 
        col = criteria.get('column') 
        col_name = f"{table_prefix}{col}"
        select_cols.append(col_name)
        value = criteria.get('value') 
        table = criteria.get('table') 

        if d_type == 'integer':
            if 'between' and 'and' in value.lower():
                value = value.replace("between", "BETWEEN")
                value = value.replace("and", "AND")
                condition = f"{col_name} {value}"

            condition = f"{col_name} {value}"
            filter_query += f" AND {condition}"

        if d_type == 'string':
            if col == 'gbe_score':
                if value.lower() == 'good':
                    condition = f"{col_name} > 15"
                if value.lower() == 'review':
                    condition = f"{col_name} >= 10 AND {col_name} <= 15"
                if value.lower() == 'bad':
                    condition = f"{col_name} < 10"
            
            if col == 'player_position_side':
                # Get the matching sides from the input
                print_colored(f"List value: {value}", "RED")
                condition = get_sides_condition(col_name,value)
            
            else:
                condition = f"{col_name} = '{value}'"

            filter_query += f" AND {condition}"

        if d_type == 'date':

            condition = build_date_condition(col_name, value)
            if condition:
                filter_query += f" AND {condition}"

        if d_type == 'bool':
            # right now the only bool variable is national_team
            
            select_cols.remove(col_name)
            # col = 'national_team_id' # Change the column name to team_id
            col_name = "vaspi.national_team_id"
            
            select_col_national_team = f"CASE WHEN {col_name} IS NOT NULL THEN TRUE ELSE FALSE END as national_team"
            select_cols.append(select_col_national_team)

            if isinstance(value, bool):
                value = str(value).lower()

            if value.lower() == "true":
                condition = f"{col_name} is not NULL"
            if value.lower() == "false":
                condition = f"{col_name} is NULL"
            
            filter_query += f" AND {condition}"

        if d_type == 'list':

            # Convert the value to a list if it is not already
            if isinstance(value, int):
                value = [value]
                #print_colored(f"List value: {value}", "GREEN")

            if isinstance(value, str):
                # Convert the string to a list using ast.literal_eval
                value = ast.literal_eval(value)
                #print_colored(f"List value: {value}", "GREEN")
    
            # Convert the list of values to a string format suitable for SQL
            values_str = ", ".join(map(str, value))
            
            # Negative condition
            negative_conditions = ['not_team_id']

            if col in negative_conditions:
                select_cols.remove(col_name)
                col = 'team_id' # Change the column name to team_id
                col_name = f"{table_prefix}{col}"
                select_cols.append(col_name)
                condition = f"{col_name} NOT IN ({values_str})"
            else:
                condition = f"{col_name}  IN ({values_str})"
            #print_colored(f"List condition: {condition}", "GREEN")
            
            filter_query += f" AND {condition}"


    # Join the columns with commas
    select_columns_str = ", ".join(select_cols)

    select_query += f", {select_columns_str}" if select_columns_str else ""
    
    final_query = select_query + " " + from_query + " " + filter_query
    
    print_colored(final_query, "GREEN")
    return final_query



def multiple_criteria_handler(response):
    session_id = response.get('Session Id')
    logger = LoggerManager.get_logger(f"user_{session_id}").get_logger()
    logger.info(f"Handling multiple criteria question...")

    ####
    criterias_output = response.get('Open Ai Criteria Output')
    criterias = criterias_output.get('criterias')
    
    # List of season_ids
    entities_info = response.get('Entities Info')
    season_info = entities_info.get('season_info')
    season_ids = [season.get('season_id') for season in season_info if season.get('season_id') is not None]

    # Convert season_ids to a comma-separated string
    season_ids_str = ", ".join(map(str, season_ids))


    compiled_criterias = compile_criteria_info(criterias,entities_info)
    response['Compiled Criterias'] = compiled_criterias

    print_colored(compiled_criterias, "CYAN")

    
        

    multiple_crit_query = add_criterias2_query(compiled_criterias,season_ids_str)

    stats_dict = criterias_output.get('statistics')

    if stats_dict:
        response, multiple_crit_query =  add_stat_filters_to_query(response, multiple_crit_query)

    else:
        # If no stats are requested then we just order by the dl_index
        multiple_crit_query += " ORDER BY vaspi.dl_index DESC"




    # Run query
    multiple_crit_data = get_db_data(multiple_crit_query,logger, limit= 20)

    table = print_table(multiple_crit_data, logger = True)
    logger.info(f"Multiple Criteria Table: \n{table}")
    logger.info("Handling multiple criteria question Finished")

    
    response['Multiple Criteria Query'] = multiple_crit_query
    response['Multiple Criteria Data'] = {'SQL Data 0': multiple_crit_data} 
    return response







question = "Who is the top scorer of La liga?" # Should return mutiple criteria = False
question = "Which players have scored more than 10 goals in the 2022 season?"
question = "Which players have scored more than 10 goals  and have less than 20 years of age in the 2022 season?"
question = "Who are the top 5 left footed center backs with the highest progressive carries per 90 in Ligue 1?"
question = "Consider my criteria, a central defender who is left footed, and aged 25 or younger. I want them to have good percentages for pass completion, progressive passes and progressive carries, i want them to be at least 6 feet tall and cost less than 50 million euros. The player must have also played in one of the top 5 european leagues. can you make a shortlist of 10 players ?"
# question = "how many passes has facundo pellisti completed in the 2022-23 season?"

question = "Give me the top 5 players with most dribbles per 90 in la liga that have less than 25 years, are at least 174cm tall and are forwards"
question = "Give me the top 5 players with most dribbles per 90 in la liga that have less than 25 years, are at least 174cm tall and are left footed"



if __name__ == "__main__":
    init_connection_pool()
    logger = LoggerManager.get_logger("M_Criteria_test").get_logger()
    response = "chat_bot/chat_responses/response_ses7_0620_115159.json"
    response = "chat_bot/chat_responses/response_ses8_0620_205713.json"
    response = "chat_bot/error_logs/error_ses8_0624_102022.json"
    response = "chat_bot/chat_responses/response_ses8_0624_151041.json"
    response = "chat_bot/chat_responses/response_ses8_0626_143324.json"

    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0627_092333.json"
    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0627_165132.json"
    response = "chat_bot/chat_responses/response_ses8_0627_173243.json"
    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0627_175938.json"
    response = "chat_bot/chat_responses/response_ses10_0628_112440.json"
    
    with open(response, 'r') as file:
        response = json.load(file)

    cleaned_response, tokens_used , total_time = player_filter_criteria(response)

    response['Open Ai Criteria Output'] = cleaned_response



    

    # Load necesary keys from the response
    
    response = multiple_criteria_handler(response)
    keys = [
        "User Question",
        "Raw Entities",
        "Entities Info",
        "Open AI Criteria Output",
        "Compiled Criteria",
        "Multiple Criteria Stats",
        "Multiple Criteria",
        "Multiple Criteria Query"]
    response = filter_response(response, keys)


    print_colored_response(response)

    write_json(response, prefix = 'multiple_criteria_', output_dir = 'chat_bot/chat_responses')

    

    close_connection_pool()
    
    
    

