import pandas as pd
import pickle
import json

# Reduce Players only to include players in the leagues of interest

leagues_of_interest_path = f"/Users/sebastianvasquez/BBA_Chatbot/entity_recognition/DB_data/leagues_matching.json"

leagues_of_interest = json.load(open(leagues_of_interest_path))

season_ids = []
for league in leagues_of_interest:
    season_ids.append(league["last_season_id"])




seasons_df = pd.read_csv("chat_bot/db_datasets/seasons.csv")

print(f"LEN SEASONS DF: {len(seasons_df)}")

# Filter seasons df to include only seasons in the leagues of interest
seasons_df = seasons_df[seasons_df["season_id"].isin(season_ids)]

# Save seasons df
seasons_df.to_csv("chat_bot/db_datasets/seasons_filtered.csv", index=False)

print(f"LEN SEASONS DF: {len(seasons_df)}")


seasons_df["name_lower"] = seasons_df["name"].str.lower()

# Mapping: name_lower → list of matching seasons
seasons_by_name = {}
for _, row in seasons_df.iterrows():
    name = row["name_lower"]
    if name not in seasons_by_name:
        seasons_by_name[name] = []
    seasons_by_name[name].append(row.to_dict())

# Mapping: season_id → full season row
seasons_by_id = seasons_df.set_index("season_id").to_dict("index")

# Save them
with open("chat_bot/db_datasets/filtered_seasons_by_name.pkl", "wb") as f:
    pickle.dump(seasons_by_name, f)

with open("chat_bot/db_datasets/filtered_seasons_by_id.pkl", "wb") as f:
    pickle.dump(seasons_by_id, f)
