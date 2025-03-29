import re
import json

def parse_md_tables(md_content):
    # Regex pattern to capture table headers and rows
    table_pattern = re.compile(r"## Table `(.+?)`\n\|(.+?)\|\n\|(.+?)\|\n((?:\|.+?\|.+?\|\n)*)", re.S)
    
    # Find all tables in the Markdown content
    tables = re.findall(table_pattern, md_content)

    # Dictionary to hold the structured data
    data = []

    for table in tables:
        table_name = table[0].strip()
        columns_text = table[3].strip().split('\n')

        # List to hold column details
        columns = []

        for column in columns_text:
            if column:
                col_name, col_type = column.split('|')[1:3]
                columns.append({'column_name': col_name.strip(), 'data_type': col_type.strip()})

        # Append table information to the data list
        data.append({
            'table_name': table_name,
            'content': {
                'columns': columns
            }
        })

    return data

def save_json(data, output_file):
    # Save the parsed data to a JSON file
    with open(output_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
        print(f"Data saved to {output_file}")

# Read the Markdown content from a file
with open('chat_bot/schemas/database_schema.md', 'r') as file:
    markdown_content = file.read()

# Parse the Markdown tables
parsed_data = parse_md_tables(markdown_content)

# Save data to JSON
save_json(parsed_data, 'chat_bot/write_db_description/output2.json')
