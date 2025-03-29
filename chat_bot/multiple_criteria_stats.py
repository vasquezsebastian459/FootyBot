import json
from print_colors import print_colored,print_colored_full_line
from config import client  # Import the client from the config module
import time
import ast
from logger_manager import LoggerManager
from run_query import get_db_data, init_connection_pool,close_connection_pool, print_table
import re
from Response import filter_response


with open('chat_bot/schemas/merged_table2col.json', 'r') as file:
    schema = json.load(file)


vaspo = schema.get('vm_agg_season_player_opta')
vaspo_cols = [col for col in vaspo]


def fut_stat_mapper(response,football_stats, temp = 0.3, max_tokens = 600):
    session_id = response.get('Session Id')
    logger = LoggerManager.get_logger(f"user_{session_id}").get_logger()

    message = f"""
    Your task is to map the football statistic to the corresponding columns in the table:

    These are the columns: {vaspo_cols}

    You should return the response like this:
    {{
    "stat1": "column_name1",
    "stat2": "column_name2",
    "stat3": "column_name3",
    }}

    for example:
    {{
    "tackles per 90 min ": "tackles_90",
    "total recoveries": "recoveries",
    "expected goal per shot": "xg_per_shot",
    }}

    Only the dict. No other text. 
    Dont make up columns. Write the column that is most similar to the resquested one.
    But never make up a column name.

    This is not a column name: "shots_on_target"

    """
    
    # Create a completion using the chat endpoint
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system",
            "content": message},
            {"role": "user",
            "content":football_stats}
        ],
        temperature=temp ,
        max_tokens = max_tokens# Default is typically 1; lower temperature for more deterministic output
    )
    # Check if there is a valid response
    if completion.choices:
        choice = completion.choices[0]
        generated_response = choice.message.content 
        print_colored(f"OPEN AI RESPONSE Fut Stat Mapper:\n{generated_response}", "YELLOW")
        logger.info(f"\nOPEN AI RESPONSE Fut Stat Mapper:\n{generated_response}")
        
        tokens_used = completion.usage.total_tokens # Get Token Usage
        print_colored(f"Tokens used: {tokens_used}", "ORANGE")
        cleaned_response = clean_and_parse_response(generated_response)
        return cleaned_response, tokens_used
    else:
        print("No completion found.")


def clean_and_parse_response(response_str):
    # Use a regular expression to find the dictionary part in the response string
    match = re.search(r"\{[\s\S]*?\}", response_str)
    
    if match:
        dict_str = match.group(0)
        try:
            # Parse the dictionary string into a Python dictionary
            parsed_dict = json.loads(dict_str.replace("'", "\""))
            return parsed_dict
        except json.JSONDecodeError as e:
            print(f"Error parsing the dictionary: {e}")
            return None
    else:
        print("No dictionary found in the response.")
        return None



def find_percentiles_stats(stats_info_list, response,logger):
    # List of season_ids
    entities_info = response.get('Entities Info')
    season_info = entities_info.get('season_info')
    season_ids = [season.get('season_id') for season in season_info]


    top_percentile = 0.70
    bottom_percentile = 0.30
    select_part = "SELECT"
    from_part = " FROM vm_agg_season_player_opta"
    where_part = " WHERE season_id in (" + ",".join([str(season_id) for season_id in season_ids]) + ");"


    for i, stat_info in enumerate(stats_info_list):
        stat = stat_info.get('stat')
        column = stat_info.get('stat_info').get('column')

        # write the percentiles used
        stats_info_list[i]['stat_info']['percentiles'] = [bottom_percentile, top_percentile]
        select_part += f" MIN({column}) AS {column}_min,"
        select_part += f" MAX({column}) AS {column}_max,"
        select_part += f" AVG({column}) AS {column}_mean,"
        select_part += f" STDDEV({column}) AS {column}_stddev,"
        select_part += f" PERCENTILE_CONT({top_percentile}) WITHIN GROUP (ORDER BY {column}) AS {column}_top_percentile,"
        select_part += f" PERCENTILE_CONT({bottom_percentile}) WITHIN GROUP (ORDER BY {column}) AS {column}_bottom_percentile"
        

        if i < len(stats_info_list) - 1:
            select_part += ","
    

    query = select_part + from_part + where_part

    data = get_db_data(query,logger)

    formated_table = print_table(data, logger= True)
    logger.info(f"Stats Metrics: \n{formated_table}")

    # Extract the single row of values
    columns , rows = data
    values_row = rows[0]

    for i, stat_info in enumerate(stats_info_list):        
        column = stat_info.get('stat_info').get('column')
        min_value = values_row[columns.index(f"{column}_min")]
        max_value = values_row[columns.index(f"{column}_max")]
        mean_value = values_row[columns.index(f"{column}_mean")]
        stddev_value = values_row[columns.index(f"{column}_stddev")]
        top_value = values_row[columns.index(f"{column}_top_percentile")]
        bottom_value = values_row[columns.index(f"{column}_bottom_percentile")]

        stat_metrics = {

            'min': round(min_value,2),
            'bottom': round(bottom_value,2),
            'mean': round(mean_value,2),
            'top': round(top_value,2),
            'max': round(max_value,2),
            'stddev': round(stddev_value,2)
        }
        #stats_info_list[i]['stat_info']['stat_metrics'] = [min_value, bottom_value, top_value, max_value]
        stats_info_list[i]['stat_info']['stat_metrics'] = stat_metrics

    return stats_info_list


def add_fut_stats2query(multiple_crit_query, stats_info_list):

    prefix = "vaspo."

    select_part,remaining_part = multiple_crit_query.split('FROM')
    remaining_part = "FROM" + remaining_part

    normalized_cols = []

    for stat in stats_info_list:
        and_condition = " AND "
        column = stat.get('stat_info').get('column')
        column_name = f"{prefix}{column}"


        # Add column to the select part
        select_part += f", {column_name}"
        
        stat_metrics = stat.get('stat_info').get('stat_metrics')

        top_percentile_value = stat_metrics.get('top')
        bottom_percentile_value = stat_metrics.get('bottom')
        min_value = stat_metrics.get('min')
        max_value = stat_metrics.get('max')
        mean_value = stat_metrics.get('mean')
        stddev_value = stat_metrics.get('stddev')
        
        threshold = stat.get('stat_info').get('threshold')
        special_case = stat.get('stat_info').get('special_case')

        if special_case:
            and_condition += special_case

        if threshold == "top":
            
            and_condition += f"{column_name} > {top_percentile_value}"

            # Calculate the normalized column
            normalize_clause = f"({column_name} - {min_value}) / ({max_value} - {min_value})" # Min-Max Normalization
            normalize_clause = f"({column_name} - {mean_value}) / {stddev_value}" # Z-Score Normalization
            normalized_cols.append(normalize_clause)
        elif threshold == "bottom":
            and_condition += f"{column_name} < {bottom_percentile_value}"
            
            # Calculate the normalized column, subtract -1 to make the 
            normalize_clause = f"(1- ({column_name} - {min_value}) / ({max_value} - {min_value}))" # Min-Max Normalization
            normalize_clause = f"-(({column_name} - {mean_value}) / {stddev_value})" # Z-Score Normalization
            normalized_cols.append(normalize_clause)
        elif threshold == "average":
            and_condition += f"{column_name} BETWEEN {bottom_percentile_value} AND {top_percentile_value}"
        else:
            #Handle special cases where threshold is between two values or with a logical operator.
            print_colored(f"Special case for {column}", "RED")
            operations = ['<=', '>=', '=', '>', '<']

            if 'between' and 'and' in threshold:
                threshold = threshold.replace('between','')
                bottom, top = threshold.split('and')
                print_colored(f"Bottom: {bottom.strip()}, Top: {top.strip()}","RED")
                and_condition += f"{column_name} BETWEEN {bottom.strip()} AND {top.strip()}"

            elif any(op in threshold for op in operations):
                for op in operations:
                    if op in threshold:
                        threshold = threshold.replace(op,'')
                        threshold = threshold.strip()
                        print_colored(f"Logical operator found in {column}", "RED")
                        and_condition += f"{column_name} {op} {threshold}"
                        print_colored(and_condition, "RED")
                        break # Break to avoid matching multiple operators
                
            
            else:
                and_condition += f"1 = 1"

        # Add the and_condition to the multiple_crit_query    
        remaining_part += and_condition 

        # add 
        #(vaspo.dribbles_total - 0) / (212 - 0)
        

    if normalized_cols:
        sum_normalized_cols = " + ".join(normalized_cols)
        sum_normalized_cols = f"({sum_normalized_cols}) AS combined_score"
        select_part += f", {sum_normalized_cols}"

        # Add the orber by clause
        remaining_part += " ORDER BY combined_score DESC"

    # Combine the select and remaining parts to form the new query
    multiple_crit_query = f"{select_part} {remaining_part}"

    return multiple_crit_query

def special_columns_condition(column,response):
    condition = "AND 1 = 1"
    if column == 'dl_index':

        session_id = response.get('Session Id')
        logger = LoggerManager.get_logger(f"user_{session_id}").get_logger()

        # List of season_ids
        entities_info = response.get('Entities Info')
        season_info = entities_info.get('season_info')
        season_ids = [season.get('season_id') for season in season_info if season.get('season_id') is not None]

        # Convert season_ids to a comma-separated string
        season_ids_str = ", ".join(map(str, season_ids))

        query = f"SELECT min((0.5*0.9*90*current_matchday)) as min_minutes_played from t_season ts where season_id IN ({season_ids_str})"

        data = get_db_data(query,logger)

        if data:
            min_minutes_played = data[1][0][0]
        else:
            min_minutes_played = 800
            
        condition = f"minutes_played > {min_minutes_played} AND "
        print_colored(f"Special condition for minutes_played: {condition}", "RED")
        return condition

            

        
def add_stat_filters_to_query(response,multiple_crit_query):
    overall_start_time = time.time()
    session_id = response.get('Session Id')
    logger = LoggerManager.get_logger(f"user_{session_id}").get_logger()

    criterias_output = response.get('Open Ai Criteria Output')
    stats_dict = criterias_output.get('statistics')

    # Initialize the list of stats_info
    stats_info_list = []
    fut_stats = []
    for stat,threshhold in stats_dict.items():
        fut_stats.append(stat)
        stats_info_list.append({
            'stat' : stat,
            'stat_info' : {
            'column': None ,
            'percentiles': None,
            'stat_metrics': None,
            'threshold': threshhold,
            'special_case': None
        }
        })


    start_time = time.time()
    # Use Open AI to map the football stats to the corresponding columns in the table. Ex: dribbling -> dribbles_total    
    fut_stats_map, tokens_used = fut_stat_mapper(response,str(fut_stats))
    response['Tokens Used']['fut_stat_mapper'] = tokens_used # Add Token Usage
    end_time = time.time() - start_time
    print_colored(f"Time taken: {end_time}", "ORANGE") 

    # Add the mapped column to the stats_info_list. Ex -> stat: dribbles, column: dribbles_total
    for i, stat_dict in enumerate(stats_info_list):
        stat  = stat_dict.get('stat') # this is the stat requested by the user. Like dribbles
        db_stat = fut_stats_map[stat] # This is the actual column in the db. Like dribbles_total

        stats_info_list[i]['stat_info']['column'] = db_stat 
        
        special_columns = ['dl_index']

        if db_stat in special_columns:
            condition = special_columns_condition(db_stat,response)
            stats_info_list[i]['stat_info']['special_case'] = condition

        
        

    print_colored(stats_info_list, "GREEN")

    # Then we find the Min, Max, Top Percentile and Bottom Percentile for each column
    stats_info_list = find_percentiles_stats(stats_info_list, response,logger)

    # Construct the query with the normalized columns and the percentiles filters
    multiple_crit_query = add_fut_stats2query(multiple_crit_query, stats_info_list)

    response['Multiple Criteria Stats'] = stats_info_list
    overall_end_time = time.time() - overall_start_time
    response['Performance Data']['Preprocessing']['add_stat_filters_to_query'] = overall_end_time
    return response, multiple_crit_query


    

if __name__ == "__main__":
    
    init_connection_pool()
    start_time = time.time()
    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0626_183651.json"
    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0627_175938.json"
    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0627_181040.json"
    response = "chat_bot/testing_responses/preprocessing/test_q_preprocess0627_181735.json"
    response = "chat_bot/chat_responses/response_ses10_0628_112440.json"
    response = "chat_bot/chat_responses/response_ses8_0628_113838.json"

    logger = LoggerManager.get_logger("M_Criteria_stats_test").get_logger()
    
    with open(response, 'r') as file:
        response = json.load(file)

    multiple_crit_query = "SELECT vaspi.player_id, vaspi.player_name, vaspi.age FROM vm_agg_season_player_info AS vaspi JOIN vm_agg_season_player_opta AS vaspo ON vaspo.player_id = vaspi.player_id  WHERE vaspi.season_id IN (816529, 816530, 816527, 816531, 816528) AND vaspo.season_id IN (816529, 816530, 816527, 816531, 816528) AND vaspi.player_id not in (60, 61, 62, 63, 64, 65, 66, 80, 81, 82, 83, 84, 85, 86, 100, 101, 102, 103, 104, 105, 106, 110, 111, 112, 113, 114, 115, 116) AND vaspi.age < 25"
    
    response, multiple_crit_query = add_stat_filters_to_query(response,multiple_crit_query)

    keys = ['Multiple Criteria Stats']
    response = filter_response(response,keys)

    end_time = time.time() - start_time
    print_colored(f"Time taken: {end_time}", "ORANGE")
    print_colored(response, "GREEN")
    print_colored(multiple_crit_query, "YELLOW")


    close_connection_pool()

