import os
import json
from collections import defaultdict
from datetime import datetime
import shutil
import logging

# Configure logging to include the timestamp
logging.basicConfig(
    filename='/Users/sebastianvasquez/BBA_Chatbot/chat_bot/cron_test.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info('Script started')

def group_responses_by_day(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    grouped_responses = defaultdict(list)

    # Read all JSON files from the input directory
    for filename in os.listdir(input_dir):
        
        if filename.endswith('.json'):
            logging.info('Reading file: %s', filename)
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r') as file:
                try:
                    response = json.load(file)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {filename}")
                    logging.info('Error decoding JSON from file: %s', filename)
                    continue

                # Extract date from filename (assuming the format is like message_MMDD_HHMMSS.json or query_MMDD_HHMMSS.json)
                parts = filename.split('_')
                if len(parts) >= 2:
                    date_str = parts[1][:4]  # Extract the MMDD part
                    try:
                        date_obj = datetime.strptime(date_str, '%m%d').replace(year=datetime.now().year)
                        date_key = date_obj.strftime('%Y-%m-%d')
                        grouped_responses[date_key].append((filename, response))
                    except ValueError:
                        print(f"Error parsing date from file: {filename}")
                        logging.info('Error parsing date from file: %s', filename)
                        continue

    # Move grouped responses into separate directories
    for date, responses in grouped_responses.items():
        date_dir = os.path.join(output_dir, date)
        os.makedirs(date_dir, exist_ok=True)

        for filename, response in responses:
            output_file_path = os.path.join(date_dir, filename)
            logging.info('Moving file to %s', output_file_path)
            # Move the file to the new directory
            shutil.move(os.path.join(input_dir, filename), output_file_path)

    print(f"Grouped responses have been saved in {output_dir}")

# Example usage
input_directory = 'chat_bot/chat_responses'
output_directory = 'chat_bot/chat_responses'
group_responses_by_day(input_directory, output_directory)

input_directory = 'chat_bot/error_logs'
output_directory = 'chat_bot/error_logs'
group_responses_by_day(input_directory, output_directory)

input_directory = 'chat_bot/temporary_logs'
output_directory = 'chat_bot/temporary_logs_test'

logging.info('Script finished')

# 53 18 * * * /Users/svasquez/driblab/dl-vision/.venv/bin/python3 /Users/svasquez/driblab/dl-vision/chat_bot/json_organizer.py
