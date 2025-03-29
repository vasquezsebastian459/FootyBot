import json
import os
import shutil
import datetime

def text_file_to_json(file_path):
    """Converts a formatted text file into a JSON structure for messages.

    Args:
        file_path (str): The path to the text file.

    Returns:
        str: The JSON string representation of the messages.
    """

    messages = []
    current_function = ""
    current_placeholders = []
    current_message = ""

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("Function:"):
                if current_function:
                    messages.append({
                        "function": current_function,
                        "placeholders": current_placeholders,
                        "message": current_message
                    })
                current_function = line.split(":")[1].strip()
                current_placeholders = []
                current_message = ""
            elif line.startswith("Placeholders:"):
                current_placeholders = [x.strip() for x in line.split(":")[1].split(",")]
            elif line.startswith("Message:"):
                # Skip the "Message:" line and start accumulating the message
                continue
            else:
                current_message += line + "\n"  # Preserve newlines

    # Add the last message
    messages.append({
        "function": current_function,
        "placeholders": current_placeholders,
        "message": current_message
    })

    return json.dumps({"messages": messages}, indent=4)

# Example usage

json_output = text_file_to_json("chat_bot/open_ai_messages/open_ai_messages.txt")

# Move current messages to a backup folder
os.makedirs("chat_bot/open_ai_messages/backup", exist_ok=True)

# Generate the current date and time
current_date = datetime.datetime.now().strftime("%m%d%H%M")

# Generate the new file name with the current date appended
new_file_name = "chat_bot/open_ai_messages/backup/open_ai_messages_" + current_date + ".json"

# Move current messages to a backup folder
shutil.move("chat_bot/open_ai_messages/open_ai_messages.json", new_file_name)

with open('chat_bot/open_ai_messages/open_ai_messages.json', "w") as file:
    file.write(json_output)
