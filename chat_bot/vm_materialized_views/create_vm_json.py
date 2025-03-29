import sys
import os
import json
import subprocess
# Get the absolute path to the directory containing `create_vm_json.py`
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory (where `run_query.py` and `print_colors.py` are located) to sys.path
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


# USE THIS COMMAND IN THE TERMINAL TO RUN THE SCRIPT:
# python -m chat_bot.vm_materialized_views.create_vm_json


# Now you can import from the parent package or sibling modules
from ..run_query import get_db_data2


# List of materialized views
materialized_views = [
    "vm_agg_season_player_all",
    "vm_agg_team_fifa",
    "vm_agg_year_team",
    "vm_det_player_gbe",
    "vm_det_player_placer",
    "vm_det_team_placer",
    "vm_fac_games_player",
    "vm_fac_player_country",
    "vm_fac_player_search_lm",
    "vm_agg_competition_team",
    "vm_agg_season_coach",
    "vm_agg_season_coach_similarity",
    "vm_agg_season_player_alert",
    "vm_agg_season_player_info",
    "vm_agg_season_player_opta",
    "vm_agg_season_player_similarity",
    "vm_agg_season_team",
    "vm_agg_season_team_opta",
    "vm_agg_season_team_similarity",
    "vm_agg_year_player_info",
    "vm_agg_year_player_loan",
    "vm_fac_transfer",
    "vm_game_missing",
    "vm_old_game_missing"
]

all_data = []

for view in materialized_views:
    try:
        query = f"""
        SELECT 
            att.attname AS column_name,
            typ.typname AS data_type
        FROM 
            pg_catalog.pg_attribute att
        JOIN 
            pg_catalog.pg_class cls ON att.attrelid = cls.oid
        JOIN 
            pg_catalog.pg_type typ ON att.atttypid = typ.oid
        WHERE 
            cls.relname = '{view}'
            AND cls.relkind = 'm'
            AND att.attnum > 0
            AND NOT att.attisdropped;
        """
        
        result = get_db_data2(query)

        # Skip header-like row if necessary
        if result and result[0] == ['column_name', 'data_type']:
            result = result[1:]

        # Reformat the result to match desired JSON structure
        formatted_result = [{'column_name': col[0], 'data_type': col[1]} for col in result[0]]

        table_info = {
            "table_name": view,
            "content": {"columns": formatted_result}
        }
        all_data.append(table_info)

        print(result[0])

        
    
    except Exception as e:
        print(f"Error processing view {view}: {e}")
        # Optionally log error details or add to a list of errors for further analysis

# Save the data to a JSON file
with open('chat_bot/vm_materialized_views/materialized_views_data.json', 'w') as f:
    json.dump(all_data, f, indent=4)
