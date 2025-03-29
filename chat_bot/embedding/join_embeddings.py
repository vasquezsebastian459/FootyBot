import pickle

# Specify the path to your pickle file
vm_all_tables_embedding_large_path = "chat_bot/embedding/open_ai_embeddings/vm_all_tables_embedding_large.pkl"

all_tables_embedding_large_path = "chat_bot/embedding/open_ai_embeddings/all_tables_embedding_large.pkl"
# Open the pickle file in read mode
with open(vm_all_tables_embedding_large_path, "rb") as file:
    # Load the data from the pickle file
    data = pickle.load(file)
    
print(f"Length of {vm_all_tables_embedding_large_path}: {len(data)}")

# Open the pickle file in read mode
with open(all_tables_embedding_large_path, "rb") as file:
    # Load the data from the pickle file
    data = pickle.load(file)
    
print(f"Length of {all_tables_embedding_large_path}: {len(data)}")
# Now you can work with the loaded data
# For example, you can print it


# JOIN EMBEDDINGS

import pickle

def join_pickle_files(pickle_file1, pickle_file2, output_file):
  """
  Joins two pickle files into a single pickle file.

  Args:
      pickle_file1 (str): Path to the first pickle file.
      pickle_file2 (str): Path to the second pickle file.
      output_file (str): Path to the output pickle file where the combined data will be saved.
  """

  with open(pickle_file1, 'rb') as f1, open(pickle_file2, 'rb') as f2, open(output_file, 'wb') as out:
    # Load data from both files
    data1 = pickle.load(f1)
    data2 = pickle.load(f2)

    # Combine the data dictionaries
    combined_data = {**data1, **data2}
    
    print(f"Length of OUTPUT: {len(combined_data)}")

    # Save the combined data to the output file
    pickle.dump(combined_data, out)

# Example usage 
pickle_file1 = "chat_bot/embedding/open_ai_embeddings/vm_all_tables_embedding_large.pkl"
pickle_file2 = "chat_bot/embedding/open_ai_embeddings/all_tables_embedding_large.pkl"
output_file = "chat_bot/embedding/open_ai_embeddings/merged_embeddings_large.pkl"

join_pickle_files(pickle_file1, pickle_file2, output_file)

print(f"Pickle files joined successfully! Combined data saved to: {output_file}")
