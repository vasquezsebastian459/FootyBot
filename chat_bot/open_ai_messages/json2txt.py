import json
import textwrap

# Define the path to your JSON file
json_file_path = 'chat_bot/open_ai_messages/open_ai_messages.json'
# Define the path for the output txt file
txt_file_path = 'chat_bot/open_ai_messages/temp_open_ai_messages.txt'
# Set the desired wrap width
wrap_width = 80

def wrap_text(text, width):
    return '\n'.join(textwrap.wrap(text, width=width))

# Read JSON data from file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Prepare the text content for the TXT file
output_lines = []
for message in data['messages']:
    function_line = f"Function: {message['function']}"
    placeholder_line = f"Placeholders: {', '.join(message['placeholders'])}\n"
    message_lines = wrap_text(message['message'], wrap_width)
    output_lines.append(function_line)
    output_lines.append(placeholder_line)
    output_lines.append(f"Message:\n{message_lines}")
    output_lines.append("")  # Add a blank line between entries

# Write the formatted text to a TXT file
with open(txt_file_path, 'w') as file:
    file.write('\n'.join(output_lines))

print(f"Formatted text has been saved to {txt_file_path}")
