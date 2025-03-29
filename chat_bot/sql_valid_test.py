import pandas as pd
from sql_query import Query
import json
from logger_manager import LoggerManager

# The schema used to feed the validate_sql_query function
# This one is different than the one used to extract the top n tables 
with open('/Users/sebastianvasquez/BBA_Chatbot/chat_bot/schemas/merged_table2col.json', 'r') as file:
    schema = json.load(file)

logger = LoggerManager.get_logger("SQL_Query_test").get_logger()

logger.info("Starting SQL Query Validation Test")
log_file_name = LoggerManager.get_log_file_name("SQL_Query_test")
print(f"Log file for SQL_Query_test: {log_file_name}")

queries_path = "chat_bot/sql_query_results.csv"


df = pd.read_csv(queries_path)
mini_df = df.head(10)

print(mini_df)

# correct_predictions = 0

# for index, row in df.iterrows():
#     query_str = row['SQL Query']
#     ground_truth = row['Valid']
#     query = Query(index, query_str, schema, logger)
#     query.display_query()
#     query.run_checks_query()
#     valid_query = query.valid
#     print(f"Ground Truth: {ground_truth}")
#     print(f"Valid Query: {valid_query}")
    
#     if valid_query == ground_truth:
#         correct_predictions += 1

# # Calculate and print accuracy
# total_queries = len(df)
# print(f"Total Queries: {total_queries}")
# print(f"Correct Predictions: {correct_predictions}")
# accuracy = correct_predictions / total_queries
# print(f"Accuracy: {accuracy * 100:.2f}%")

# Define a function to apply to each row
def validate_query(row):
    query_str = row['SQL Query']
    query = Query(row.name, query_str, schema, logger)
    query.display_query()
    query.run_checks_query()
    return query.valid

# Apply the function to each row and create a new column 'Predicted Valid'
df['Predicted Valid'] = df.apply(validate_query, axis=1)

# Calculate the accuracy
accuracy = (df['Valid'] == df['Predicted Valid']).mean()
print(f"Accuracy: {accuracy * 100:.2f}%")

# Calculate Type I and Type II errors
type1_errors = ((df['Valid'] == True) & (df['Predicted Valid'] == False)).sum()
type2_errors = ((df['Valid'] == False) & (df['Predicted Valid'] == True)).sum()

# Calculate True Positives, True Negatives, False Positives, and False Negatives
true_positives = ((df['Valid'] == True) & (df['Predicted Valid'] == True)).sum()
true_negatives = ((df['Valid'] == False) & (df['Predicted Valid'] == False)).sum()
false_positives = ((df['Valid'] == False) & (df['Predicted Valid'] == True)).sum()
false_negatives = ((df['Valid'] == True) & (df['Predicted Valid'] == False)).sum()

# Calculate percentages
total = len(df)
true_positives_percent = (true_positives / total) * 100
true_negatives_percent = (true_negatives / total) * 100
false_positives_percent = (false_positives / total) * 100
false_negatives_percent = (false_negatives / total) * 100

# Print the confusion matrix
print("\nConfusion Matrix:")
print(f"True Positives (TP): {true_positives} ({true_positives_percent:.2f}%)")
print(f"True Negatives (TN): {true_negatives} ({true_negatives_percent:.2f}%)")
print(f"False Positives (FP): {false_positives} ({false_positives_percent:.2f}%)")
print(f"False Negatives (FN): {false_negatives} ({false_negatives_percent:.2f}%)")

# Create a DataFrame for the confusion matrix
confusion_matrix = pd.DataFrame({
    '': ['Predicted True', 'Predicted False'],
    'Actual True': [true_positives, false_negatives],
    'Actual False': [false_positives, true_negatives]
})

print("\nAccuracy Table:")
print(confusion_matrix)

# Write the updated DataFrame to a new CSV file
updated_csv_path = "chat_bot/sql_query_predicted_results.csv"
df.to_csv(updated_csv_path, index=False)
print(f"Updated CSV file: {updated_csv_path}")


# Type I Error (False Positive): The model predicted the query to be valid, but it was invalid
# Type II Error (False Negative): The model predicted the query to be invalid, but it was valid
# We want to minimize the Type II errors which can lead to a potential loss of SQL data to answer a question

