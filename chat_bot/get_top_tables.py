
import requests
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from run_chatbot import Chatbot



class TopTables:
    def __init__(self, chatbot: 'Chatbot'):
        self.chatbot = chatbot

        self.top_n = 5

    def get_embedding_openai(self, text):
        """Generate embedding for the input text using OpenAI."""
        response = self.chatbot.client.embeddings.create(
        input=text,
        model="text-embedding-3-large"      #"text-embedding-3-small"
    )
        return np.array(response.data[0].embedding)  # Convert the embedding to a NumPy array

    def calc_cosine_sim(self, user_embedding):
        # Calculate similarity scores and sort tables based on similarity
        similarity_scores = {}
        for table, table_embedding in self.chatbot.openai_embeddings.items():
            
            similarity = cosine_similarity([user_embedding], [table_embedding])[0][0]
            similarity_scores[table] = similarity

        return similarity_scores
    

    def retrieve_topn_tables_keywords(self, similarity_scores):
    
        # Create a dictionary where keys are table names and values are descriptions
        table_descriptions = {table['table']: table['description'] for table in self.chatbot.merged_tables_descriptions}
        
        # Get the top n tables based on similarity scores
        top_tables = sorted(similarity_scores.items(), key=lambda item: item[1], reverse=True)[:self.top_n]

        # Create an output list that includes the table name, score, and description
        output_with_descriptions = [(table, score, table_descriptions[table]) for table, score in top_tables]

        return output_with_descriptions
    
    def extract_tables_from_schema(self, tables):

        self.top_tables_names = [table[0] for table in tables]

        # Filter the tables based on your list of table names
        filtered_tables = [table for table in self.chatbot.full_schema if table["table_name"] in self.top_tables_names]

        return filtered_tables
    
    def extract_table2col(self):
        table_names = [name.split('.')[-1] for name in self.top_tables_names]
        table2cols_shortlist = []
        for table,col in self.chatbot.all_tables2col.items():
            if table in table_names:
                table_dict = {'table_name': table, 'columns': col}
                table2cols_shortlist.append(table_dict)
                print()
        return table2cols_shortlist

    
    def enhance_sim_scores(self, similarity_scores):
        entity = self.chatbot.user_intention.entity_of_interest.lower()
        agg = self.chatbot.user_intention.aggregation.lower()

        enhanced_scores = {}
        for table, base_score in similarity_scores.items():
            table_lower = table.lower()

            boost = 0.0
            if entity in table_lower:
                boost += 0.05
            if agg in table_lower:
                boost += 0.05

            enhanced_scores[table] = base_score + boost

        return enhanced_scores
        

    def run(self):

        embeddings = self.get_embedding_openai(self.chatbot.question)
        sim_scores = self.calc_cosine_sim(embeddings)

        enhanced_sim_scores = self.enhance_sim_scores(sim_scores)

        top_tables = self.retrieve_topn_tables_keywords(enhanced_sim_scores)
        self.top_tables = self.extract_tables_from_schema(top_tables)
        
        return self.top_tables

        
        

    

if __name__ == "__main__":
    from run_chatbot import Chatbot
    from get_user_intention import UserIntention
    question = "How many goals does Kylian Mbappe have for Real Madrid this season?"

    chatbot = Chatbot()
    chatbot.load_data()
    chatbot.question = question

    user_intention = UserIntention(chatbot)

    user_intention.run()

    
    print(user_intention.valid_question)
    print(user_intention.entity_of_interest)
    print(user_intention.aggregation)

    chatbot.user_intention.valid_question = user_intention.valid_question
    chatbot.user_intention.entity_of_interest = user_intention.entity_of_interest
    chatbot.user_intention.aggregation = user_intention.aggregation


    top_tables_extractor = TopTables(chatbot)

    top_tables = top_tables_extractor.run()
    print(top_tables_extractor.top_tables_names)
    