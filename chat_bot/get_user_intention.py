from typing import TYPE_CHECKING
import requests
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


if TYPE_CHECKING:
    from run_chatbot import Chatbot


class UserIntention:
    def __init__(self, chatbot: 'Chatbot'):
        self.chatbot = chatbot
        
        self.valid_question = None
        self.entity_of_interest = None
        self.aggregation = None

        

    def question_classifier(self, temp = 0.3, max_tokens = 600):
    
        # Extract the open ai prompt from  the JSON file at chat_bot/open_ai_messages/open_ai_messages.json
        message = self.chatbot.utils.get_formatted_message('question_classifier', [self.context])
        
        # Create a completion using the chat endpoint
        completion = self.chatbot.client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system",
                "content": message},
                {"role": "user",
                "content":self.question}
            ],
            temperature=temp ,
            max_tokens = max_tokens# Default is typically 1; lower temperature for more deterministic output
        )

        # Check if there is a valid response
        if completion.choices:
            
            choice = completion.choices[0]
            response = choice.message.content 
            
            # Get Token Usage
            tokens_used = completion.usage.total_tokens

            if "False" in response:
                return False, tokens_used
            else:
                return True , tokens_used
        else:
            print("No completion found.")






    def run(self):

        self.question = self.chatbot.question
        self.context = self.chatbot.context        
        
        # Extract User's Entity of Interest
        start_time = time.time()
        res = requests.post("http://localhost:5005/predict_entity_of_interest", json={"question": self.question})
        self.entity_of_interest = res.json()['prediction']
        end_time = time.time()
        print(f"Time taken to entity of interest: {end_time - start_time} seconds")

        # Extract User's Aggregation
        start_time = time.time()
        res = requests.post("http://localhost:5005/predict_aggregation", json={"question": self.question})
        self.aggregation = res.json()['prediction']
        end_time = time.time()
        print(f"Time taken to aggregation: {end_time - start_time} seconds")
        


if __name__ == "__main__":
    from run_chatbot import Chatbot

    chatbot = Chatbot()
    chatbot.load_data()
    question = "How many goals does Kylian Mbappe have for Real Madrid this season?"
    user_intention = UserIntention(chatbot)

    chatbot.question = question

    user_intention.run()

    
    print(user_intention.valid_question)
    print(user_intention.entity_of_interest)
    print(user_intention.aggregation)


    