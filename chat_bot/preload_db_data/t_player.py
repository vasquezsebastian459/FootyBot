import pandas as pd
import pickle
import json


# Reduce Players only to include players in the leagues of interest

leagues_of_interest_path = f"/Users/sebastianvasquez/BBA_Chatbot/entity_recognition/DB_data/leagues_matching.json"

leagues_of_interest = json.load(open(leagues_of_interest_path))

season_ids = []
for league in leagues_of_interest:
    season_ids.append(league["last_season_id"])

print(season_ids)


# Load players df

players_df = pd.read_csv("chat_bot/db_datasets/players.csv")

print(f"LEN PLAYERS DF: {len(players_df)}")

# Filter players df to include only players in the leagues of interest
players_df = players_df[players_df["last_season_id"].isin(season_ids)]


# Save players df
players_df.to_csv("chat_bot/db_datasets/players_filtered.csv", index=False)


print(f"LEN PLAYERS DF: {len(players_df)}")


players_df["name_lower"] = players_df["name"].str.lower()

# Mapping: name_lower → list of matching players
players_by_name = {}
for _, row in players_df.iterrows():
    name = row["name_lower"]
    if name not in players_by_name:
        players_by_name[name] = []
    players_by_name[name].append(row.to_dict())

# Mapping: player_id → full player row
players_by_id = players_df.set_index("player_id").to_dict("index")

# Save them
with open("chat_bot/db_datasets/filtered_players_by_name.pkl", "wb") as f:
    pickle.dump(players_by_name, f)

with open("chat_bot/db_datasets/filtered_players_by_id.pkl", "wb") as f:
    pickle.dump(players_by_id, f)