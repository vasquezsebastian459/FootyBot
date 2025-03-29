import json
from openai import OpenAI
from config import client  # Import the client from the config module

# This file is used to generate descriptions for the materialized views in the database
# Only run once!

def run_chat_query(table, write_file = True, temp = 1, max_tokens = 600):
    # client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": f"""
             Your task is to write a description of the following table. Take into context that these are tables of a database of a football analytics company.
             Always return the description in dictionary format like bellow:
             
                "table": "public.det_shot",
                "description": "This table records detailed shot events in football matches, capturing data about each shot such as the player who took it, the team, match specifics, timing within the match, shot coordinates, expected goals (xG) value, and more. It provides a comprehensive dataset for analyzing shot effectiveness and player performance in specific game situations."
                

            """
            },
            {"role": "user", "content": f"table name: {table['table_name']} \n table columns: {table['content']['columns']}"}
        ],
        temperature=temp , # Default is typically 1; lower temperature for more deterministic output
        max_tokens= max_tokens  # Max tokens to generate
    )

    choice = completion.choices[0]
    response = choice.message.content 
    return response

# Open the JSON file
with open('chat_bot/vm_materialized_views/materialized_views_data.json') as file:
    data = json.load(file)


descriptions = []
# Loop through the data
for table in data:
    try:
        response = run_chat_query(table)
        parsed_response = json.loads(response)
        descriptions.append(parsed_response)
        print(f'Generated description for table: {table["table_name"]}')
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON for table: {table['table_name']}. Error: {str(e)}")
        # Optionally, append a placeholder or error message in the descriptions list
        descriptions.append({'table': table['table_name'], 'error': 'Failed to parse JSON', 'details': str(e)})
    except Exception as e:
        print(f"An error occurred for table: {table['table_name']}. Error: {str(e)}")
        # Handle other types of exceptions that may occur

# Save the responses to a JSON file
with open('chat_bot/vm_materialized_views/vm_table_description.json', 'w') as json_file:
    json.dump(descriptions, json_file, indent=4)
    print("Responses have been saved to chat_bot/write_db_description/all_tables_descriptions.json")
