import json

# Specify the path to your JSON file
file_path = "chat_bot/embedding/reduced_schema/base_reduced_schema_nospace.json"

# Open the JSON file
with open(file_path, "r") as file:
    # Load the JSON data
    data = json.load(file)

# Generate a data type dictionary to map data types to shorter identifiers
def create_data_type_dictionary(data):
    unique_data_types = set()
    for table in data:
        for column in table["content"]["columns"]:
            unique_data_types.add(column["data_type"])
    return {dtype: idx for idx, dtype in enumerate(unique_data_types)}

# Abbreviate keys and replace data types using the dictionary
def abbreviate_and_normalize(data, data_type_dict):
    result = []
    for table in data:
        new_table = {
            "tbl": table["table_name"],
            "cols": []
        }
        for column in table["content"]["columns"]:
            abbreviated_column = {
                "col": column["column_name"],
                "dt": data_type_dict[column["data_type"]]
            }
            new_table["cols"].append(abbreviated_column)
        result.append(new_table)
    return result

def optimize_schema(data):
    # Create the data type dictionary
    data_type_dict = create_data_type_dictionary(data)

    # Apply abbreviation and normalization
    abbreviated_normalized_data = abbreviate_and_normalize(data, data_type_dict)

    # Prepare the optimized JSON output
    optimized_data = {
        "data_types": data_type_dict,
        "tables": abbreviated_normalized_data
    }

    # # Print or save the optimized JSON
    # print(json.dumps(optimized_data, indent=4))

    # Optionally save to a file
    with open('chat_bot/embedding/reduced_schema/optimized_schema.json', 'w') as f:
        json.dump(optimized_data, f,separators=(',', ':'))

    return optimized_data

def optimize_schema2(data):
    # Create the data type dictionary
    data_type_dict = create_data_type_dictionary(data)

    # Apply abbreviation and normalization
    abbreviated_normalized_data = abbreviate_and_normalize(data, data_type_dict)

    # Prepare the optimized JSON output
    optimized_data = {
        "data_types": data_type_dict,
        "tables": abbreviated_normalized_data
    }

    # # Print or save the optimized JSON
    # print(json.dumps(optimized_data, indent=4))

    # Optionally save to a file
    with open('chat_bot/embedding/reduced_schema/optimized_schema.json', 'w') as f:
        json.dump(optimized_data, f,separators=(',', ':'))

    return data_type_dict,abbreviated_normalized_data


reduced_opt_schema = optimize_schema(data)

table_names = [table['tbl'] for table in reduced_opt_schema['tables']]
print(table_names)
def convert_to_array_format(schema):
    # Extract and map data types to integers
    data_types = {v: k for k, v in schema['data_types'].items()}
    # Transform each table and its columns into array format
    array_tables = []
    for table in schema['tables']:
        table_name = table['tbl']
        cols = [table_name]  # Start array with table name
        cols.extend([ [col['col'], data_types[col['dt']]] for col in table['cols']])  # Append columns as sub-arrays
        array_tables.append(cols)
    return array_tables

# Convert schema
# array_schema = convert_to_array_format(data)

# # Output the array schema
# print(json.dumps(array_schema, indent=4))

# # Optionally save to a file
# with open('chat_bot/embedding/reduced_schema/array_schema.json', 'w') as f:
#     json.dump(array_schema, f,separators=(',', ':'))
