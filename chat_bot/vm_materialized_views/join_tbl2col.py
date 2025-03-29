# This file is to join both the tabl2col.json containning all the regular tables information and
# the vm_table2col.json containing all the materialized views information

# We will do the same with  all_tables_descriptions.json

import json


tbl2col_path = 'chat_bot/schemas/table2col.json'
vm_tbl2col_path = 'chat_bot/vm_materialized_views/vm_table2col.json'

# Load the first JSON file
with open(tbl2col_path, 'r') as f:
    tbl2col = json.load(f)

# Load the second JSON file
with open(vm_tbl2col_path, 'r') as f:
    vm_tbl2col = json.load(f)

# Update the first JSON file with the second JSON file
tbl2col.update(vm_tbl2col)

# Write the updated JSON file
with open('chat_bot/schemas/merged_table2col.json', 'w') as f:
    json.dump(tbl2col, f, indent=4)

table_descriptions_path = 'chat_bot/schemas/all_tables_descriptions.json'
vm_table_descriptions_path = 'chat_bot/vm_materialized_views/vm_all_tables_descriptions.json'


# Load the first JSON file
with open(table_descriptions_path, 'r') as f:
    table_descriptions = json.load(f)

# Load the second JSON file
with open(vm_table_descriptions_path, 'r') as f:
    vm_table_descriptions = json.load(f)


# Combine the lists from both JSON files
merged_tables_descriptions = table_descriptions + vm_table_descriptions

# Write the updated JSON file
with open('chat_bot/schemas/merged_tables_descriptions.json', 'w') as f:
    json.dump(merged_tables_descriptions, f, indent=4)

