import time

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from run_chatbot import Chatbot


# This class is reponsible of:
# - adding more info to the SQL Data retreived
# - Generating a final response


class PostProcessing:
    def __init__(self, chatbot: 'Chatbot'):
        self.chatbot = chatbot



    def get_key_info(self, sql_data):
        columns, data_rows = sql_data

        if 'Database error' in columns:
            return [columns, data_rows]
        
        # Dictionary to store column indices and corresponding new column names and extraction functions
        info_config = {
            'player_id': {
                'new_column': 'player_name',
                'func': self.chatbot.key_info_extractor.extract_playername
            },
            'match_id': {
                'new_column': 'match_teams',
                'func': self.chatbot.key_info_extractor.extract_match_id_teams
            },
            'team_id': {
                'new_column': 'team_name',
                'func': self.chatbot.key_info_extractor.get_team_name
            }
        }

        # Append new columns if they are not already in the columns list
        for key, config in info_config.items():
            if key in columns and config['new_column'] not in columns:
                columns.append(config['new_column'])

        new_data_rows = []
        for row in data_rows:
            modified_row = list(row)  # Start by copying the original row
            modification_made = False

            for key, config in info_config.items():
                if key in columns:
                    index = columns.index(key)  # Get the index dynamically
                    new_value = config['func'](row[index])  # Call the extraction function
                    modified_row.append(new_value)
                    modification_made = True

            new_data_rows.append(modified_row)

        return [columns, new_data_rows]


    def add_key_info(self, response):
        # Here we will add the columns to the data we have collected so far
        start_time = time.time()
        sql_data = response['SQL Data']

        for data_label, data_results in sql_data.items():
            if "Invalid SQL" in data_results or "Database error" in data_results:
                continue
            else:
                modified_data = self.get_key_info(data_results)
                sql_data[data_label] = modified_data

        response['Performance Data']['run_chat_bot_time']['add_key_info_new'] = time.time() - start_time
        response['SQL Data'] = sql_data

        return response
    

    def run_chat_explanation(self, output, temp = 1, max_tokens = 600):
        
        user_question = output['User Question']
        key_info_context = output['Key Information Context']
        sql_query = output['SQL Query']
        sql_output = output['SQL Data']
        # client = OpenAI()
        
        # Extract message content from the JSON file
        place_holders = [user_question, key_info_context, sql_query, sql_output]
        message = self.chatbot.utils.get_formatted_message('run_chat_explanation', place_holders)
        
        # Create a completion using the chat endpoint
        completion = self.chatbot.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system",
                "content": message},
                {"role": "user",
                "content": user_question}
            ],
            temperature=temp , # Default is typically 1; lower temperature for more deterministic output
            max_tokens= max_tokens  # Max tokens to generate
        )
        # Check if there is a valid response
        if completion.choices:
            choice = completion.choices[0]
            response = choice.message.content 

            tokens_used = completion.usage.total_tokens
            
            output["Tokens Used"]['chat_explanation'] = tokens_used
            output["Generated Explanation"] = response

            return output
                
        else:
            print("No completion found.")

    def run(self, response):

        # Add key info to the SQL Data
        response = self.add_key_info(response)
        
        # Generate a final response
        response = self.run_chat_explanation(response)

        # We leave the entities link empty for now
        response['Entities Link'] = {}

        return response
        