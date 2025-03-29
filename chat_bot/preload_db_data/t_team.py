import pandas as pd
import pickle
import json



# Reduce Players only to include players in the leagues of interest

leagues_of_interest_path = f"/Users/sebastianvasquez/BBA_Chatbot/entity_recognition/DB_data/leagues_matching.json"

leagues_of_interest = json.load(open(leagues_of_interest_path))

season_ids = []
for league in leagues_of_interest:
    season_ids.append(league["last_season_id"])





teams_df = pd.read_csv("chat_bot/db_datasets/teams.csv")

print(f"LEN TEAMS DF: {len(teams_df)}")

# Filter teams df to include only teams in the leagues of interest
teams_df = teams_df[teams_df["last_season_id"].isin(season_ids)]

# Save teams df
teams_df.to_csv("chat_bot/db_datasets/teams_filtered.csv", index=False)

print(f"LEN TEAMS DF: {len(teams_df)}")



teams_df["name_lower"] = teams_df["team_name"].str.lower()

print(f"teams_df: {teams_df.columns}")




# Mapping: name_lower → list of matching teams
teams_by_name = {}
for _, row in teams_df.iterrows():
    name = row["name_lower"]
    if name not in teams_by_name:
        teams_by_name[name] = []
    teams_by_name[name].append(row.to_dict())

# Mapping: team_id → full team row
teams_by_id = teams_df.set_index("team_id").to_dict("index")

# Save them
with open("chat_bot/db_datasets/filtered_teams_by_name.pkl", "wb") as f:
    pickle.dump(teams_by_name, f)

with open("chat_bot/db_datasets/filtered_teams_by_id.pkl", "wb") as f:
    pickle.dump(teams_by_id, f)
