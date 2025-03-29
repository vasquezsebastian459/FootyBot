import json

full_schema_path = 'chat_bot/vm_materialized_views/vm_database_schema.json'
with open(full_schema_path) as file:
    schema = json.load(file)
    
print(len(schema))


full_schema_path = 'chat_bot/schemas/database_schema.json'
with open(full_schema_path) as file:
    schema2 = json.load(file)
    
print(len(schema2))

def update_jsons(json1, json2):
  """
  Updates the first JSON object with new information from the second JSON object.

  Args:
      json1 (dict): The first JSON object.
      json2 (dict): The second JSON object.

  Returns:
      dict: The updated JSON object.
  """

  for table_name, content in json2.items():  # Use items() for key-value pairs
    if table_name not in json1:
      json1[table_name] = content.copy()
    else:
      # Update all keys in content, not just "content"
      json1[table_name].update(content)


# # Example usage
print(type(schema))
print(type(schema2))
# merged_data = update_jsons(schema, schema2)

merged_data = schema + list(schema2)  
print(len(merged_data))

with open('chat_bot/vm_materialized_views/merged_schema.json', 'w') as file:
    json.dump(merged_data, file, indent=4)
