import pickle
import json

def filter_pickle_by_tables(embeddings_path, tables_to_keep, output_file):
  """
  Filters a pickle file, keeping only the specified tables and saving the filtered data.

  Args:
      pickle_file (str): Path to the embeddings file.
      tables_to_keep (list): List of table names to keep in the output.
      output_file (str): Path to the output pickle file containing the filtered data.
  """

  with open(embeddings_path, 'rb') as f, open(output_file, 'wb') as out:
    # Load data from the pickle file
    data = pickle.load(f)

    # Filter data by keeping only specified tables
    filtered_data = {key: value for key, value in data.items() if key in tables_to_keep}

    # Save the filtered data to the output file
    pickle.dump(filtered_data, out)

# Example usage (replace with your actual file paths)
embeddings_path = "chat_bot/embedding/open_ai_embeddings/merged_embeddings_large.pkl"
output_file = "chat_bot/embedding/open_ai_embeddings/merged_filtered_embeddings.pkl"

# Load the list of tables to keep from a JSON file
with open(embeddings_path, 'rb') as file:
    tables = pickle.load(file)

table_names = list(tables.keys())
print(type(table_names))
print(table_names)
print(len(table_names))

# Starting Point: 368 tables

# Extract vm_tables:

vm_tables = []
for table in table_names:
    if "vm_" in table:
        vm_tables.append(table)

print(vm_tables)
print(len(vm_tables))


# Add VT tables that include game data

vt_game_tables = []
for table in table_names:
    if "vt_" in table and "game" in table:
        vt_game_tables.append(table)

print(vt_game_tables)
print(len(vt_game_tables))

# Add Physical data
physical_tables = ['public.agg_season_player_pd','public.agg_game_player_pd']

# Add score data 
score_tables = ['public.vt_season_score_player','public.vt_game_score_player']

# Add t_tables as needed
t_tables = ['public.t_goal']

# Group all tables
tables_to_keep = vm_tables + vt_game_tables + physical_tables + score_tables + t_tables

print(tables_to_keep)
print(len(tables_to_keep))

# Save these tables

with open('chat_bot/schemas/tables2keep.json', 'w') as file:
    json.dump({"tables": tables_to_keep}, file,indent=4)

# Filter the tables by keeping only the specified tables
with open('chat_bot/schemas/tables2keep.json') as file:
    tables_to_keep = json.load(file)
    tables_to_keep = tables_to_keep['tables']
# tables_to_keep = ["vm_det_player_gbe", "vm_det_player_placer"]  # Replace with desired tables


# Filter the embeddings file with the tables to keep file.
filter_pickle_by_tables(embeddings_path, tables_to_keep, output_file)

print(f"Pickle file filtered! Filtered data saved to: {output_file}")

# Load the filtered pickle file and check the length and keys
with open(output_file, "rb") as file:
    # Load the data from the pickle file
    data = pickle.load(file)
    
print(f"Length of {output_file}: {len(data)}")

print(f"Data keys: {data.keys()}")
