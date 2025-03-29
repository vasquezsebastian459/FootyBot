import json
import os

def search_json_files(directory, search_query):
    """
    Search for JSON files in the given directory that contain the specified user question substring.
    
    Args:
    directory (str): The directory to search in.
    search_query (str): The user question substring to search for in the JSON files.
    
    Returns:
    list of str: A list of filenames that contain the specified user question substring.
    """
    matching_files = []  # List to hold the names of matching files
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):  # Ensure the file is a JSON file
                file_path = os.path.join(root, file)  # Get the full path of the file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)  # Load the JSON data from the file
                        # Convert entire JSON object into a string
                        json_str = json.dumps(data).lower()  # Convert to string and make case-insensitive

                        # Check if the search query is in the JSON string
                        if search_query.lower() in json_str:
                            matching_files.append(file)  # Add file to the list if it matches
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {file}")
                except Exception as e:
                    print(f"Unexpected error with file {file}: {str(e)}")

    return matching_files

# Directory containing the JSON files
directory_path = 'chat_bot/chat_responses'

# The specific query to search for
query = "qualifier"

# Call the function and print the results
found_files = search_json_files(directory_path, query)
print("Matching files:", found_files)
