import pickle
import json
import numpy as np
from openai import OpenAI
from config import client  # Import the client from the config module

def get_embedding(text):
    """Generate embedding for the input text using OpenAI."""
    # client = OpenAI()
    response = client.embeddings.create(
    input=text,
    model="text-embedding-3-large"   #"text-embedding-3-small"
)
    return np.array(response.data[0].embedding)  # Convert the embedding to a NumPy array

def save_embeddings(input_json_path, output_pickle_path):
    # Load JSON file
    with open(input_json_path, 'r') as file:
        schema_json = json.load(file)

    # Generate embeddings for each table description and save them
    embeddings = {}
    for table in schema_json:
        print('Generating embedding for:', table['table'])
        description = table['description']  # Get the description text
        embedding = get_embedding(description)
        embeddings[table['table']] = embedding  # Save the embedding as a numpy array

    # Save the embeddings dictionary to a file using pickle
    with open(output_pickle_path, 'wb') as file:
        pickle.dump(embeddings, file)
        print(f"Embeddings have been saved to {output_pickle_path}")

# For normal tables
input_json_path = 'chat_bot/write_db_description/all_tables_descriptions.json'
output_pickle_path = 'chat_bot/embedding/open_ai_embeddings/all_tables_embedding_large.pkl'

# For vm tables 

input_json_path = 'chat_bot/vm_materialized_views/vm_all_tables_descriptions.json'
output_pickle_path = 'chat_bot/embedding/open_ai_embeddings/vm_all_tables_embedding_large.pkl'
save_embeddings(input_json_path, output_pickle_path)
