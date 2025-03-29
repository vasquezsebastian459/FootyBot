import json
from datetime import datetime
import os
from custom_json_encoder import CustomEncoder
from colorama import Fore, Style
from typing import TYPE_CHECKING
import traceback
if TYPE_CHECKING:
    from run_chatbot import Chatbot


class Utils:
    def __init__(self, chatbot: 'Chatbot'):
        self.chatbot = chatbot
        

    def get_formatted_message(self,function_name, placeholders):
        """
        This function reads a JSON containing messages, finds the message with a specific function name,
        and formats its content using the provided placeholders.

        Args:
            function_name (str): The name of the function to search for.
            placeholders (list): A list of placeholder names to be replaced.

        Returns:
            str: The formatted message content or None if not found.
        """

        # Load JSON data containing messages
        with open('chat_bot/open_ai_messages/open_ai_messages.json') as file:
            data = json.load(file)

        # Extract messages list from the data (handle potential absence)
        messages = data.get("messages", [])

        # Find message with matching function name
        target_message = [message for message in messages if message["function"] == function_name]
        # Extract placeholder names from the target message
        placeholder_names = target_message[0]["placeholders"]

        
        if len(placeholders) != len(placeholder_names):
                output_message = f"Warning: Placeholders do not match for function '{function_name}'."
                print(output_message)
                return output_message  # Return the unformatted message

        # Check if a message was found
        if target_message:
            
            message_content = target_message[0]["message"]
            
            # Create a dictionary for formatted placeholders (assuming placeholders match)
            formatted_placeholders = dict(zip(placeholder_names, placeholders))

            # Check if placeholders are defined in the message metadata
            if "placeholders" in target_message[0]:
                
                # Format message content using the dictionary
                return message_content.format(**formatted_placeholders)
            else:
                # Placeholders might not be defined or might not match message structure
                # Consider logging a warning or handling this case differently
                print(f"ERROR with '{function_name}'.")
                return target_message[0]["message"]  # Return the unformatted message
        else:
            return None
        
    

    def write_json(self, data, prefix= 'response_', output_dir = 'chat_bot/chat_responses'):

        try:
        
            # Create a unique file name using current date and time
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            file_name = f"{prefix}{timestamp}.json"

            output_path = os.path.join(output_dir, file_name)

            # Write the response and token usage to a file
            with open(output_path, 'w') as file:
                json.dump(data, file, indent=4, cls = CustomEncoder)  # Writing JSON data with pretty print
                print(Fore.YELLOW +f"Data has been successfully saved to {output_path}" + Style.RESET_ALL)

        except Exception as e:
            print(f"Error writing JSON: {str(e)}")
            traceback.print_exc()

