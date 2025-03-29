from print_colors import print_colored, print_colored_full_line
import json
from datetime import datetime
import os
from custom_json_encoder import CustomEncoder


def filter_response(dictionary, keys):
    """
    Helper function to filter Response by a list of keys
    """
    return {key: dictionary[key] for key in keys if key in dictionary}


def print_colored_response(response, color= "YELLOW"):
    """
    Helper function to print a colored response
    """
    for key, value in response.items():
        print_colored(f"{key}:", color)
        print_colored(value, color)
        print()

def write_json(data,prefix= 'response_', output_dir = 'chat_bot/chat_responses'):
    
    # Create a unique file name using current date and time
    timestamp = datetime.now().strftime("%m%d_%H%M%S")
    file_name = f"{prefix}{timestamp}.json"
    output_path = os.path.join(output_dir, file_name)

    # Write the response and token usage to a file
    with open(output_path, 'w') as file:
        json.dump(data, file, indent=4, cls = CustomEncoder)  # Writing JSON data with pretty print
        print_colored(f"Data has been successfully saved to {output_path}", "YELLOW")
        
if __name__ == "__main__":

    json_file = "chat_bot/chat_responses/response_ses7_0620_115159.json"

    with open(json_file, 'r') as file:
        response = json.load(file)

    keys = ['User Question', 'User Intention']
    filtered_response = filter_response(response, keys)
    print_colored_response(filtered_response)