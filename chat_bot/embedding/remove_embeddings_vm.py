import pickle

# Load embeddings from the pkl file
with open('chat_bot/embedding/open_ai_embeddings/vm_all_tables_embedding_large.pkl', 'rb') as f:
    embeddings = pickle.load(f)
embeddings_to_remove = []

# Filter out embeddings you want to keep
filtered_embeddings = {key: value for key, value in embeddings.items() if key not in embeddings_to_remove}
# Save the filtered embeddings to a new pickle file
with open('chat_bot/embedding/open_ai_embeddings/vm_reduced_tables_embeddings.pkl', 'wb') as f:
    pickle.dump(filtered_embeddings, f)

print(f"Original number of tables: {len(embeddings)}")
print(f"Number of tables after removal: {len(filtered_embeddings)}")