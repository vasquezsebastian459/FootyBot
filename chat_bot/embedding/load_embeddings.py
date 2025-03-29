import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
from openai import OpenAI
from config import client  # Import the client from the config module



def get_embedding_openai(text):
    """Generate embedding for the input text using OpenAI."""
    # client = OpenAI()
    response = client.embeddings.create(
    input=text,
    model="text-embedding-3-large"      #"text-embedding-3-small"
)
    return np.array(response.data[0].embedding)  # Convert the embedding to a NumPy array

def calculate_similarity(user_embedding, embeddings_path):
    # Load the embeddings from the pickle file
    with open(embeddings_path, 'rb') as file:
        loaded_embeddings = pickle.load(file)

    # Calculate similarity scores and sort tables based on similarity
    similarity_scores = {}
    for table, table_embedding in loaded_embeddings.items():
        
        similarity = cosine_similarity([user_embedding], [table_embedding])[0][0]
        similarity_scores[table] = similarity

    return similarity_scores

def retrieve_topn_tables(similarity_scores, top_n=5):
    # Load JSON file
    with open('chat_bot/schemas/merged_tables_descriptions.json', 'r') as file:
        joined_tables_data = json.load(file)

    # Create a dictionary where keys are table names and values are descriptions
    table_descriptions = {table['table']: table['description'] for table in joined_tables_data}
    
    # Get the top n tables based on similarity scores
    top_tables = sorted(similarity_scores.items(), key=lambda item: item[1], reverse=True)[:top_n]

    # Create an output list that includes the table name, score, and description
    output_with_descriptions = [(table, score, table_descriptions[table]) for table, score in top_tables]

    return output_with_descriptions





def extract_tables_from_schema(tables,full_schema_path, write_output = False):

    table_names = [table[0] for table in tables]
    # Extract relevant tables from the schema
    # Read Json File with the schema
    with open(full_schema_path) as file:
        schema = json.load(file)

    # Filter the tables based on your list of table names
    filtered_tables = [table for table in schema if table["table_name"] in table_names]


    if write_output: # Write filtered tables to a JSON file
        with open('chat_bot/embedding/reduced_schema/reduced_schema_nospace.json', 'w') as file:
            json.dump(filtered_tables, file,separators=(',', ':')) # Removes unnecessary spaces after commas and colons like {"key": "value"} into {"key":"value"}.


    return filtered_tables


def get_top_tables(embeddings_path, user_question,full_schema_path, top_n=5):
    # Generate the embedding for the user's question
    user_embedding = get_embedding_openai(user_question)

    # Calculate similarity scores
    similarity_scores = calculate_similarity(user_embedding, embeddings_path)

    # Retrive the top n tables
    top_tables = retrieve_topn_tables(similarity_scores,top_n=top_n)

    # Extract relevant tables from the schema
    schema_tables = extract_tables_from_schema(top_tables,full_schema_path, write_output = True)

    # tables = [table[0] for table in top_tables] # get the table names from the top_tables list
    return schema_tables


# Embeddings
openai_embeddings_path = 'chat_bot/embedding/open_ai_embeddings/reduced_tables_embeddings.pkl'

#json file with the schema

full_schema_path = 'chat_bot/schemas/database_schema.json'
# User's question
user_question = "How many expected points has team id 88"
user_question = "How much possesion did team id 55 have in the game against team id 77"
user_question = "How many goasl were scored in the last Real Madrid vs Barcelona game "

user_question = "Can you perform game-specific metrics for football team id 54"

# schema_tables = get_top_tables(openai_embeddings_path, user_question,full_schema_path)

# print(schema_tables)

# for table in tables:
#     print('top_tables:',table[0])
# schema_tables = extract_tables_from_schema(tables,full_schema_path, write_output = True)
# print("Filtered Tables:",schema_tables)f