import json


def create_table2columns_dict2(schema_path):
    with open(schema_path, 'r') as file:
        document_text = file.read()

    # Parse the document into schema
    schema = {}
    current_table = None

    for line in document_text.split('\n'):
        # Check for a table header
        if line.startswith('## Table `'):
            current_table = line.split('`')[1]
            schema[current_table] = []
        elif '|' in line and not line.strip().startswith('| ------------'):
            parts = line.split('|')
            if len(parts) > 1:
                column_name = parts[1].strip()
                if column_name not in ["Column Name", "Data Type"]:  # Skip header and divider lines
                    schema[current_table].append(column_name)
                    

    return schema

# vm_schema_path = 'chat_bot/vm_materialized_views/vm_database_schema.md'
# vm_schema = create_table2columns_dict2(vm_schema_path)
# vm_schema = {key.split('.')[1]: value for key, value in vm_schema.items() if len(key.split('.')) > 1} # THis removes the public. from the table name or any name before "."

# # Writing JSON data
# filename = 'chat_bot/vm_materialized_views/vm_table2col.json'
# with open(filename, 'w') as f:
#     json.dump(vm_schema, f, indent=4)  # Use 'indent' for pretty-printing

