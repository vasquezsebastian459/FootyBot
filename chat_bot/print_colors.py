from colorama import Fore, Style, init,Back
from pprint import pformat
import shutil
# Initialize colorama
init(autoreset=True)

# HOW TO CONSTRUCT THE COLOR CODE:
# \033[38;5;<color code>m
# Example: ORANGE CODE = 208
# SO: \033[38;5;208m
# Dictionary to map color names to colorama Fore colors
color_dict = {
    "BLACK": Fore.BLACK,
    "RED": Fore.RED, #ERRORS
    "GREEN": Fore.GREEN, # INTERACTION WITH WEBPAGE
    "YELLOW": Fore.YELLOW, # FOR EACH NEW KEY ADDED
    "BLUE": Fore.BLUE,
    "MAGENTA": Fore.MAGENTA, # JSON FILE UPDATE
    "CYAN": Fore.CYAN, # FOR SQL QUERIES
    "WHITE": Fore.WHITE,
    "RESET": Fore.RESET,
    "BRIGHT_RED": Fore.LIGHTRED_EX,
    "BRIGHT_GREEN": Fore.LIGHTGREEN_EX,
    "BRIGHT_YELLOW": Fore.LIGHTYELLOW_EX,
    "BRIGHT_BLUE": Fore.LIGHTBLUE_EX,
    "BRIGHT_MAGENTA": Fore.LIGHTMAGENTA_EX,
    "BRIGHT_CYAN": Fore.LIGHTCYAN_EX,
    "BRIGHT_WHITE": Fore.LIGHTWHITE_EX,
    "BACKGROUND_RED": Back.RED,
    "BACKGROUND_GREEN": Back.GREEN,
    "BACKGROUND_YELLOW": Back.YELLOW,
    "BACKGROUND_BLUE": Back.BLUE,
    "BACKGROUND_MAGENTA": Back.MAGENTA,
    "BACKGROUND_CYAN": Back.CYAN,
    "BACKGROUND_WHITE": Back.WHITE,
    "ORANGE": "\033[38;5;208m",  # PERFORMACE DATA
    "BACKGROUND_ORANGE": "\033[48;5;208m",
}

def print_colored(message, color="RESET",style = False):
    # Get the color from the dictionary, default to Fore.RESET if color is not found
    color_code = color_dict.get(color.upper(), Fore.RESET)
    
    # Pretty-print the message if it's a dictionary
    # if isinstance(message, dict):
    #     message = pformat(message, indent=4)
    
    if isinstance(message, dict) and style:
        formatted_message = format_dict_as_list(message)
        print(f"{color_code}{formatted_message}{Style.RESET_ALL}")
    else:
        print(f"{color_code}{message}{Style.RESET_ALL}")

def format_dict_as_list(data, indent=0):
    formatted = ""
    for key, value in data.items():
        formatted += '  ' * indent + f"- {key}: "
        if isinstance(value, dict):
            formatted += "\n" + format_dict_as_list(value, indent + 1)
        else:
            formatted += f"{value}\n"
    return formatted

def print_colored_full_line(text, color):
    term_width = shutil.get_terminal_size().columns
    padded_text = text.ljust(term_width)
    color_code = getattr(Back, color, Back.RESET)
    print(f"{color_code}{padded_text}{Style.RESET_ALL}")

# Your text to be printed
text = "This is a full line with a cyan background."

# Print the text with a cyan background
print_colored_full_line("", "CYAN")
# Example usage
user_intention = {"player": "Daley Sinkgraven", "action": "top scorer"}

# # Normal print
# print_colored(f"USER INTENTION (Normal): {user_intention}", "YELLOW")

# # Pretty print
# print_colored("USER INTENTION (Pretty):", "YELLOW")
# print_colored(user_intention, "YELLOW")

# # Pretty-printing a dictionary
# entities_dict = {
#     'players': {
#         'Daley Sinkgraven': {
# 'id': 151980,            'start_pos': 58,
#  'end_pos': 74,
#             'link': 'https://pro.driblab.com/player/151980'
#         }
#     },
#     'teams': {
#         'UD Las Palmas': {
#         'id': 14350,
#     'start_pos': 80,            'end_pos': 93,'link': 'https://pro.driblab.com/team/14350'
#         }
#     },
#     'seasons': {
#         'La Liga 2023': 816527
#     }
# }

# # Normal print
# print_colored(f"Entities Link (Normal): {entities_dict}", "GREEN")

# # Pretty print
# print_colored("Entities Link (Pretty):", "BRIGHT_GREEN")
# print_colored("Entities Link (Pretty):", "GREEN")
# print_colored("Entities Link (Pretty):", "BACKGROUND_GREEN")
# print_colored(entities_dict, "GREEN")
