import traceback
from extract_keyinfo import KeyInfoExtractor
from performance import Performance
import time
import pickle
from datetime import datetime
import json
from custom_json_encoder import CustomEncoder
from colorama import Fore, Style
import os
from utils import Utils
from performance import Performance
from get_user_intention import UserIntention
from get_top_tables import TopTables
from openai import OpenAI
import spacy
from query_runner import QueryRunner
from run_query import get_db_data, init_connection_pool,close_connection_pool
from post_processing import PostProcessing

class Chatbot:
    def __init__(self):
        self.question = None
        self.context = None

        self.key_info_extractor = KeyInfoExtractor(self)
        self.performance = Performance()
        self.utils = Utils(self)
        self.user_intention = UserIntention(self)
        self.top_tables_extractor = TopTables(self)
        self.query_runner = QueryRunner(self)
        self.post_processing = PostProcessing(self)

        # Initialize the OpenAI client as a global variable
        self.client = OpenAI()

        # Initialize the spaCy model as a global variable

    
        self.nlp = spacy.load("en_core_web_sm")

        # self.connection_pool = init_connection_pool()
        
    def load_data(self):

        # Set important Paths
        self.openai_embeddings_path = 'chat_bot/embedding/open_ai_embeddings/merged_filtered_embeddings.pkl'

        with open(self.openai_embeddings_path, 'rb') as f:
            start_time = time.time()
            self.openai_embeddings = pickle.load(f)
            end_time = time.time()
            print(f"Time taken to load openai embeddings: {end_time - start_time} seconds")

        
            

        self.full_schema = json.load(open('chat_bot/schemas/merged_schema.json'))

        self.all_tables2col = json.load(open('chat_bot/schemas/merged_table2col.json'))

        with open('chat_bot/open_ai_messages/table_instructions.json', 'r') as file:
            self.tables_instructions = json.load(file)['tables']

        self.merged_tables_descriptions = json.load(open('chat_bot/schemas/merged_tables_descriptions.json'))

        # Create a dictionary where keys are table names and values are descriptions
        self.table_descriptions = {table['table']: table['description'] for table in self.merged_tables_descriptions}

    def write_json(data,prefix= 'response_', output_dir = 'chat_bot/chat_responses'):
    
        # Create a unique file name using current date and time
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        file_name = f"{prefix}{timestamp}.json"
        output_path = os.path.join(output_dir, file_name)

        # Write the response and token usage to a file
        with open(output_path, 'w') as file:
            json.dump(data, file, indent=4, cls = CustomEncoder)  # Writing JSON data with pretty print
            print(Fore.YELLOW +f"Data has been successfully saved to {output_path}" + Style.RESET_ALL)


    def run(self, question, context):

        self.performance.start_overall_time = time.time()

        self.question = question
        self.context = context

        self.key_info_extractor.key_info = self.key_info_extractor.update_key_info_context(context)

        response = {}

        start_time = time.time()
        self.key_info_extractor.run()

        # Check if the key information is related to football by seeing if there are relevant entities in the key information
        if self.key_info_extractor.is_key_info_empty():
            return {
                "response": "The question is not related to football.",
                "keyinfo_context": self.context,
                "links_info": {}
            }

        print(f"Augmented Key Info: {self.key_info_extractor.augmented_key_info}")
        
        end_time = time.time()

        self.performance.extract_key_info_time = end_time - start_time

        # Check if the key information is valid
        is_valid, confirmation_info = self.key_info_extractor.valid_keyinfo()


        print(f"IS KEY INFO VALID: {is_valid}")
        print(f"CONFIRMATION INFO: {confirmation_info}")

        if not is_valid:
            
            confirmation_message = str(confirmation_info[0])
            updated_context = str(confirmation_info[1])

            # self.write_json(response, prefix='response_')

            return {
                "response": confirmation_message,
                "keyinfo_context": updated_context,
                "links_info": {}
            }
        

        # Extract the User Intention
        start_time = time.time()
        self.user_intention.run()
        end_time = time.time()
        self.performance.get_user_intention_time = end_time - start_time

        print(f"Valid Question: {self.user_intention.valid_question}")
        print(f"Entity of Interest: {self.user_intention.entity_of_interest}")
        print(f"Aggregation: {self.user_intention.aggregation}")
        print(f"User Intention Time: {self.performance.get_user_intention_time}")

        # Early return if the question is not valid

        if not self.user_intention.valid_question:
            # self.chatbot.performance.tokens_used['question_classifier'] = QC_tokens_used
            return {
                'response': "Sorry this question is not about football. Please ask a question related to football.",
                'keyinfo_context': self.context,
                'links_info': {}
            }


        # If there is no Key Information extracted, ask the user to be more specific
        if not self.key_info_extractor.augmented_key_info:

            self.performance.extract_key_info_time = end_time - start_time

            response['Generated Explanation'] = "Sorry could you be more specific? Please provide a season, team or player!"
            
            self.write_json(response, prefix = 'response_')
            # stop_logging(monitor_thread)
            return {
                'response': response['Generated Explanation'],
                'keyinfo_context': response['Previous Context'],
                'links_info': {}
            }
        
        # Get the top tables
        start_time = time.time()
        top_tables = self.top_tables_extractor.run()
        end_time = time.time()
        print(f"Top Tables Time: {end_time - start_time}")
        # self.performance.get_top_tables_time = end_time - start_time
        print(self.top_tables_extractor.top_tables_names)


        # Run the query
        start_time = time.time()
        response = self.query_runner.run({}, top_tables)
        end_time = time.time()
        print(f"Query Runner Time: {end_time - start_time}")

        # Post Processing
        start_time = time.time()
        response = self.post_processing.run(response)
        end_time = time.time()
        print(f"Post Processing Time: {end_time - start_time}")

        try:
            self.utils.write_json(response)
        except Exception as e:
            print(f"Error writing JSON: {str(e)}")
            traceback.print_exc()

        return {
                'response': response['Generated Explanation'],
                'keyinfo_context': self.context,
                'links_info': {}
            }

if __name__ == "__main__":
    service = Chatbot()

    service.load_data()

    # question = "How many goals did Harry Kane score in the Bundesliga this season?"
    question = "How many times has Barak Obama flown to the moon?"
    question = "How many tackles does Antonio Rudiger have for Real Madrid this season?"
    context = {}

    output = service.run(question, context)

    print(output)