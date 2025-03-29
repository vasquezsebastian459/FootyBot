import json


# Function to convert JSON schema to the desired array format
def convert_to_array_format(json_data):
    result = []
    for table in json_data:
        table_name = table['table_name']
        columns = table['content']['columns']
        table_array = [table_name] + [[col['column_name'], col['data_type']] for col in columns]
        result.append(table_array)
    return result



# # Specify the path to your JSON file
file_path = "chat_bot/embedding/reduced_schema/reduced_schema2.json"

# Open the JSON file
with open(file_path, "r") as file:
    # Load the JSON data
    data = json.load(file)

# Convert and store the result
array_representation = convert_to_array_format(data)
# Optionally, save the array format to a file
with open('chat_bot/embedding/reduced_schema/transformed_schema.json', 'w') as file:
    json.dump(array_representation, file,separators=(',', ':'))

table_names = [table[0] for table in array_representation]
print(table_names)