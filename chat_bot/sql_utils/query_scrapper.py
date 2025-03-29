import os
import json
import csv

def extract_sql_queries_from_json(directory):
    sql_queries = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as json_file:
                    try:
                        data = json.load(json_file)

                        if isinstance(data, list):
                            data = data[0]
                        # Assuming 'SQL Query' is the key in the JSON containing the list of queries
                        queries = data.get('SQL Query', [])
                        if isinstance(queries, list):
                            sql_queries.extend(queries)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from file {file_path}: {e}")

    return sql_queries

def write_queries_to_csv(queries, csv_file_path):
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['SQL Query'])  # Write the header
        for query in queries:
            writer.writerow([query])

def main():
    directory = 'chat_bot/chat_responses'  # Update this to your directory path
    csv_file_path = 'chat_bot/sql_queries.csv'  # Update this to your desired CSV file path

    sql_queries = extract_sql_queries_from_json(directory)
    write_queries_to_csv(sql_queries, csv_file_path)
    print(f"SQL queries have been written to {csv_file_path}")

if __name__ == "__main__":
    main()