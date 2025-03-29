import requests
import time
from run_query import get_db_data, init_connection_pool,close_connection_pool
import pandas as pd
from rapidfuzz import fuzz
import pickle
from entity_validator import EntityValidator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from run_chatbot import Chatbot


class KeyInfoExtractor:
    def __init__(self, chatbot: 'Chatbot'):
        print(f"🆕 Creating KeyInfoExtractor instance: {id(self)}")
        self.chatbot = chatbot
        self.initialized = False
        
        print("⚙️ Initializing KeyInfoExtractor ...")
        print(f"🔧 Initializing instance: {id(self)}")

        self.question = self.chatbot.question
        self.context = self.chatbot.context

        self.init_dfs()
        self.initialized = True


        self.entity_validator = EntityValidator(self)
        print("✅ KeyInfoExtractor fully initialized.")

    

    def _load_pickle(self, file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
        
    def init_dfs(self):
        self.players_df = pd.read_csv('chat_bot/db_datasets/players_filtered.csv')
        self.teams_df = pd.read_csv('chat_bot/db_datasets/teams_filtered.csv')
        self.seasons_df = pd.read_csv('chat_bot/db_datasets/seasons_filtered.csv')

        
        # Lowercase name for safer matching

        print(f"Lowering player names ...")
        start_time = time.time()
        self.players_df["name_lower"] = self.players_df["name"].str.lower()
        print(f"Time taken to lower player names: {time.time() - start_time} seconds")

        print(f"Loading precomputed entity mappings ...")
        # Load player mappings
        self.players_by_name = self._load_pickle("chat_bot/db_datasets/filtered_players_by_name.pkl")
        self.players_by_id = self._load_pickle("chat_bot/db_datasets/filtered_players_by_id.pkl")

        # Load team mappings
        self.teams_by_name = self._load_pickle("chat_bot/db_datasets/filtered_teams_by_name.pkl")
        self.teams_by_id = self._load_pickle("chat_bot/db_datasets/filtered_teams_by_id.pkl")

        # Load season mappings        
        self.seasons_by_name = self._load_pickle("chat_bot/db_datasets/filtered_seasons_by_name.pkl")
        self.seasons_by_id = self._load_pickle("chat_bot/db_datasets/filtered_seasons_by_id.pkl")
        


    def is_key_info_empty(self):
        key_info = self.key_info_list[0]
        return all((v is None or (hasattr(v, '__len__') and len(v) == 0)) for v in key_info.values())
    
    def valid_keyinfo(self):
        valid = True
        # Check each dictionary in the list for the key 'confirm' with value True
        for context in self.augmented_key_info:
            if isinstance(context, dict) and context.get('confirm') == True:

                message = context.get('Message')
                prev_ques = {'Previous Question': self.question}
                self.augmented_key_info.append(prev_ques)
                valid = False


                return valid, (message, self.augmented_key_info)
            
        return valid, None

    
    
    def extract_player_id(self, player_name):
        name_lower = player_name.lower()
        if name_lower in self.players_by_name:
            # Return the first match — or add logic to score them
            return self.players_by_name[name_lower][0]["player_id"]
        return None

    
    def extract_teamid_by_player(self, player_id):

        player_info = self.players_by_id.get(player_id)
        if player_info:
            return player_info['team_id']
        return None

    
    def extract_playername(self, player_id):
        player_info = self.players_by_id.get(player_id)
        if player_info:
            return player_info['name']
        return None

    
    def get_team_id(self, team_name):
        name_lower = team_name.lower()
        if name_lower in self.teams_by_name:
            return self.teams_by_name[name_lower][0]["team_id"]
        return None
    

    def get_season_id(self, team_id):
        team_info = self.teams_by_id.get(team_id)
        if team_info:

            print(f"Team Info: {team_info}")
            last_season_id = (
                int(team_info['last_season_id']) if pd.notna(team_info['last_season_id']) else None
            )
            last_cont_season_id = (
                int(team_info['last_cont_season_id']) if pd.notna(team_info['last_cont_season_id']) else None
            )
            return last_season_id, last_cont_season_id
        return None, None

    
    def get_team_name(self, team_id):
        team_info = self.teams_by_id.get(team_id)
        if team_info:
            return team_info['team_name']
        return None

    
    def get_season_id_by_name(self, season_name:str):
        name_lower = season_name.lower()
        if name_lower in self.seasons_by_name:
            return self.seasons_by_name[name_lower][0]["season_id"]
        return None
    
    def get_season_name(self, season_id):
        season_info = self.seasons_by_id.get(season_id)
        if season_info:
            return season_info['name']
        return None

    def extract_match_id_teams(self, match_id):
        query = f"select home_team_id, away_team_id from t_match where match_id = {match_id};"
        match_teams_id = get_db_data(query)
        home, away = match_teams_id[1][0]
        home_team_name = self.get_team_name(home)
        away_team_name = self.get_team_name(away)
        result = f"{home_team_name} - {away_team_name}"
        return  result

    def extract_keyinfo(self, key_entities):
        print(f"Key Entities 3: {key_entities}")

        overall_start = time.time()
        keyinfo = []

        for entity in key_entities:
            print(f"ENTITY: {entity}")

            # PLAYER HANDLING
            if entity['player_name']:
                print(f"PLAYER: {entity['player_name']}")
                player_names = entity['player_name']
                if isinstance(player_names, str):
                    player_names = [player_names]

                for player in player_names:
                    print(f"- PLAYER: {player}")

                    start_time = time.time()
                    player_name = self.entity_validator.validate_player_name(player, key_entities)
                    print(f"Time to validate player name: {time.time() - start_time:.3f}s")

                    player_id = None
                    if player_name['confirm']:
                        keyinfo.append(player_name)
                        continue
                    else:
                        player_id = player_name['closest_match_id']
                        player_name = player_name['closest_match']

                    if player_id is None:
                        print(f"THIS SHOULD NEVER HAPPEN!!")
                        player_id = self.extract_player_id(player_name)

                    # DB calls for team and seasons
                    teamid = self.extract_teamid_by_player(player_id)
                    re_season_id, con_season_id = self.get_season_id(teamid)
                    team_name = self.get_team_name(teamid)
                    re_season_name = self.get_season_name(re_season_id) if re_season_id else None
                    con_season_name = self.get_season_name(con_season_id) if con_season_id else None
                    

                    player_info = {
                        'player_id': player_id,
                        'team_id': teamid,
                        'team_name': team_name,
                        'regular_season_id': re_season_id,
                        'regular_season_name': re_season_name,
                        'continental_season_id': con_season_id,
                        'continental_season_name': con_season_name,
                    }
                    keyinfo.append({'player': player_name, 'info': player_info})

            # TEAM HANDLING
            if entity['team_name']:
                team_names = entity['team_name']
                if isinstance(team_names, str):
                    team_names = [team_names]

                for team in team_names:
                    print(f"- TEAM: {team}")

                    start_time = time.time()
                    team_name = self.entity_validator.validate_team_name(team, key_entities)
                    print(f"Time to validate team name: {time.time() - start_time:.3f}s")

                    if team_name['confirm']:
                        keyinfo.append(team_name)
                        continue
                    else:
                        team_name = team_name['closest_match']
                    if team_name is None:
                        continue

                    
                    teamid = self.get_team_id(team_name)
                    re_season_id, con_season_id = self.get_season_id(teamid)
                    re_season_name = self.get_season_name(re_season_id) if re_season_id else None
                    con_season_name = self.get_season_name(con_season_id) if con_season_id else None
                    

                    team_info = {
                        'team_id': teamid,
                        'regular_season_id': re_season_id,
                        'regular_season_name': re_season_name,
                        'continental_season_id': con_season_id,
                        'continental_season_name': con_season_name,
                    }
                    keyinfo.append({'team': team_name, 'info': team_info})

            # SEASON HANDLING
            if entity['season_name']:
                season_names = entity['season_name']

                for season_name in season_names:

                    start_time = time.time()
                    season_id = self.get_season_id_by_name(season_name) if season_name else None
                    print(f"Time to fetch season ID: {time.time() - start_time:.3f}s")

                    season_info = {
                        'season_id': season_id,
                        'season_name': season_name
                    }
                    keyinfo.append({'season': season_name, 'info': season_info})

        print(f"Total time in extract_keyinfo: {time.time() - overall_start:.3f}s")
        return keyinfo
    
    
    def get_entities(self):

        doc = requests.post("http://localhost:5005/entity_recognition", json={"question": self.question})
        doc = doc.json()
        entities = doc['entities']
        return entities
    

    def get_final_entities(self):

        entities = self.get_entities()
        print(f"Entities: {entities}")

        for entity in entities:
            if entity[1] == "PLAYER":
                print(f"Person: {entity[0]}")
                self.key_info["player_name"].append(entity[0])
            
            elif entity[1] == "TEAM":
                print(f"Team: {entity[0]}")
                self.key_info["team_name"].append(entity[0])
            
            elif entity[1] == "LEAGUE":


                print(f"League: {entity[0]}")
                start_time = time.time()
                # league = self.match_league_combined(entity[0])
                res = requests.post("http://localhost:5005/match_league", json={"query": entity[0], "threshold": 0.5})
                league = res.json()['matched_league']
                print(f"Time taken to match league: {time.time() - start_time} seconds")
                print(f"League: {league}")

                # Get the year of the league
                year = 2024
                for entity in entities:
                    if entity[1] == "YEAR":
                        year = entity[0]
                        break

                # Get season name
                country_code = league["country_code"]
                season_name = f"{country_code} I {year}"
                print(f"Season: {season_name}")
                self.key_info["season_name"].append(season_name)


            elif entity[1] == "YEAR":
                print(f"Year: {entity[0]}")
                self.key_info["year"].append(entity[0])

    def update_key_info_context(self, context):

        key_info = {
            "player_name": [],
            "team_name": [],
            "season_name": [],
            "country_name": [],
            "year": [],
            "division": [],
            "statistic_name": []
            }

        for key, value in context.items():

            if key == "players" and value is not None:
                plyrs_dict = value
                for plyr_name, _ in plyrs_dict.items():
                    key_info["player_name"].append(plyr_name)
            elif key == "teams" and value is not None:
                teams_dict = value
                for team_name, _ in teams_dict.items():
                    key_info["team_name"].append(team_name)

            elif key == "seasons" and value is not None:
                seasons_dict = value
                for season_name, _ in seasons_dict.items():
                    key_info["season_name"].append(season_name)

        return key_info

   

# THIS IS THE NEW VERSION OF THE KEY INFO EXTRACTOR
    def run(self):

        self.question = self.chatbot.question
        self.context = self.chatbot.context

        self.get_final_entities()


        self.key_info_list = [self.key_info]


        print(f"Key Info: {self.key_info_list}")

        # Add the new key information to the context to the response dictionary
        self.augmented_key_info = self.extract_keyinfo(self.key_info_list)


        return self.augmented_key_info
    




    

        
        

    


if __name__ == "__main__":

    response = {}
    question = "Quien es el mejor defensor de la ligue 1"
    question = "Cuantos goles tiene Lionel Messi en la liga española"
    question = "How many goals does Vinicus have for Real Madrid in la liga??"
    question = "How many goals has Kylian Mbappe scored for Real Madrid"

    response['User Question'] = question

    extractor = KeyInfoExtractor()
    extractor.run(response)
