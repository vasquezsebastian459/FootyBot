from rapidfuzz import fuzz
import time 


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from chat_bot.extract_keyinfo import KeyInfoExtractor



class EntityValidator:

    def __init__(self, key_info_extractor: 'KeyInfoExtractor'):
        self.key_info_extractor = key_info_extractor

        self.players_df = self.key_info_extractor.players_df
        self.teams_df = self.key_info_extractor.teams_df
        self.seasons_df = self.key_info_extractor.seasons_df

        self.players_by_name = self.key_info_extractor.players_by_name
        self.players_by_id = self.key_info_extractor.players_by_id

        self.teams_by_name = self.key_info_extractor.teams_by_name
        self.teams_by_id = self.key_info_extractor.teams_by_id
        
    
            

    def validate_player_name(self, player_name, key_entities):
        team_names = key_entities[0]['team_name']
        season_names = key_entities[0]['season_name']

        if isinstance(season_names, str):
            season_names = [season_names]

        # Flatten all players into a list
        all_players = []
        for player_list in self.players_by_name.values():
            all_players.extend(player_list)

        scored_players = []
        for player in all_players:
            # Use pre-lowered names
            name_score = fuzz.ratio(player_name.lower(), player['name_lower'])

            team_priority = 15 if team_names and player['team_name'] in team_names else 0
            season_priority = 10 if season_names and player['last_season_name'] in season_names else 0

            final_score = name_score + team_priority + season_priority

            scored_players.append({
                "name": player['name'],
                "player_id": player['player_id'],
                "team_name": player['team_name'],
                "last_season_name": player['last_season_name'],
                "nationality": player.get('nationality', ''),
                "final_score": final_score
            })

        # Sort and take top 5
        top_matches = sorted(scored_players, key=lambda x: x['final_score'], reverse=True)[:5]
        print(f"Top matches: {top_matches}")

        closest_match = top_matches[0]

        if closest_match['final_score'] >= 70:
            return {
                "confirm": False,
                "score": int(closest_match['final_score']),
                "inputed_name": player_name,
                "closest_match": closest_match['name'],
                "closest_match_id": closest_match['player_id']
            }
        else:
            message = f"I'm not sure about the player '{player_name}'.\nWhich of these are you referring to?\n"
            for match in top_matches:
                message += f"{match['name']} from {match['team_name']}\n"

            return {
                "confirm": True,
                "score": int(closest_match['final_score']),
                "inputed_name": player_name,
                "closest_matches": top_matches,
                "Message": message.strip()
            }

    from rapidfuzz import fuzz

    def validate_team_name(self, team_name, key_entities):
        player_names = key_entities[0]['player_name']
        season_names = key_entities[0]['season_name']

        print(f"TEAM NAME: {team_name}")
        print(f"PLAYER NAMES: {player_names}")
        print(f"SEASON NAMES: {season_names}")

        if isinstance(season_names, str):
            season_names = [season_names]

        # Flatten all teams from teams_by_name
        all_teams = []
        for team_list in self.teams_by_name.values():
            all_teams.extend(team_list)

        scored_teams = []
        for team in all_teams:
            distance = fuzz.ratio(team_name.lower(), team['name_lower'])
            season_priority = 20 if season_names and team['last_season_name'] in season_names else 0
            final_score = distance + season_priority

            scored_teams.append({
                "team_id": team['team_id'],
                "team_name": team['team_name'],
                "alias": team.get('alias', ''),
                "last_season_name": team['last_season_name'],
                "country": team.get('country', ''),
                "final_score": final_score
            })

        # Sort by final_score descending
        top_matches = sorted(scored_teams, key=lambda x: x['final_score'], reverse=True)[:5]
        print(f"Top Matches: {top_matches}")

        closest_match = top_matches[0]

        if closest_match['final_score'] >= 85:
            return {
                "confirm": False,
                "score": int(closest_match['final_score']),
                "inputed_name": team_name,
                "closest_match": closest_match['team_name']
            }
        else:
            # Construct message for user
            message = f"I'm not sure about that team name '{team_name}'.\nWhich of these are you referring to?\n"
            for match in top_matches:
                message += f"{match['team_name']} from {match['last_season_name']}\n"

            return {
                "confirm": True,
                "score": int(closest_match['final_score']),
                "inputed_name": team_name,
                "closest_matches": top_matches,
                "Message": message.strip()
            }



if __name__ == "__main__":

    from run_chatbot import Chatbot
    from extract_keyinfo import KeyInfoExtractor

    chatbot = Chatbot()

    # Make empyt lass

    
    key_info_extractor = KeyInfoExtractor(chatbot)
    entity_validator = EntityValidator(key_info_extractor)
    entities = [{'player_name': ['mbappe'], 'team_name': [], 'season_name': [], 'country_name': [], 'year': [], 'division': [], 'statistic_name': []}]

    start_time = time.time()
    validated_entity = entity_validator.validate_player_name("mbappe", entities)
    end_time = time.time()
    print(f"Time taken to validate entity: {end_time - start_time} seconds")
    print(f"validated_entity: {validated_entity}")

    # Validate team name
    start_time = time.time()
    validated_entity = entity_validator.validate_team_name("rea madid", entities)
    end_time = time.time()
    print(f"Time taken to validate entity: {end_time - start_time} seconds")
    print(f"validated_entity: {validated_entity}")
