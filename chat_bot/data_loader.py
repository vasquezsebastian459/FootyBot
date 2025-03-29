from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import json
import pickle
import time
import spacy
from sentence_transformers import SentenceTransformer
import os
import io  
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.preprocessing import LabelEncoder
import torch


class DataLoaderService:
    def __init__(self):
        self.initialized = False
        self.initialize()

    def initialize(self):
        print("Initializing DataLoaderService ...")
        print(f"Instance ID: {id(self)}")

        self.leagues_matching = self._load_json("entity_recognition/DB_data/leagues_matching.json")
        self.leagues = self._load_json("entity_recognition/DB_data/leagues_matching.json")
        self.combined_embeddings = np.load("entity_recognition/DB_data/l_combined_embeddings.npz", allow_pickle=True)
        self.combined_model = SentenceTransformer("intfloat/multilingual-e5-base")
        self.entity_recognition_model = spacy.load("entity_recognition/ner_models/model_trf/model-last")


        # Entity of interest model  
        self.entity_interest_tokenizer = AutoTokenizer.from_pretrained("user_intention/models/results_e/checkpoint-306") 
        self.entity_interest_model = AutoModelForSequenceClassification.from_pretrained("user_intention/models/results_e/checkpoint-306" )
        self.entity_interest_model.eval()  # Set model to evaluation mode

        # Load label encoder classes for entity of interest model
        self.entity_interest_le = LabelEncoder()
        self.entity_interest_le.classes_ = np.load("user_intention/models/results_e/label_classes.npy", allow_pickle=True)

        # Aggregation model
        self.agg_tokenizer = AutoTokenizer.from_pretrained("user_intention/models/results_agg/checkpoint-306") 
        self.agg_model = AutoModelForSequenceClassification.from_pretrained("user_intention/models/results_agg/checkpoint-306")
        self.agg_model.eval()  # Set model to evaluation mode

        # Load label encoder classes for aggregation model
        self.agg_le = LabelEncoder()
        self.agg_le.classes_ = np.load("user_intention/models/results_agg/label_classes.npy", allow_pickle=True)

        self.init_dfs()
        self.initialized = True
        print("✅ DataLoaderService fully initialized.")

    def _load_json(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def _load_pickle(self, path):
        with open(path, "rb") as f:
            return pickle.load(f)

    def init_dfs(self):
        print("Loading DataFrames and mappings...")

        self.players_df = pd.read_csv("chat_bot/db_datasets/players.csv")
        self.teams_df = pd.read_csv("chat_bot/db_datasets/teams.csv")
        self.seasons_df = pd.read_csv("chat_bot/db_datasets/seasons.csv")

        self.players_df["name_lower"] = self.players_df["name"].str.lower()

        self.players_by_name = self._load_pickle("chat_bot/db_datasets/players_by_name.pkl")
        self.players_by_id = self._load_pickle("chat_bot/db_datasets/players_by_id.pkl")
        self.teams_by_name = self._load_pickle("chat_bot/db_datasets/teams_by_name.pkl")
        self.teams_by_id = self._load_pickle("chat_bot/db_datasets/teams_by_id.pkl")
        self.seasons_by_name = self._load_pickle("chat_bot/db_datasets/seasons_by_name.pkl")
        self.seasons_by_id = self._load_pickle("chat_bot/db_datasets/seasons_by_id.pkl")

        self.openai_embeddings = self._load_pickle('chat_bot/embedding/open_ai_embeddings/merged_filtered_embeddings.pkl')

    def get_entities(self, question):
        doc = self.entity_recognition_model(question)
        return [(ent.text, ent.label_) for ent in doc.ents]
    
    def match_league_combined(self, input_text, threshold=0.5):
        print(f"Input Text: {input_text}")
        input_text = input_text.lower().strip()
        input_text = f"query: {input_text}"

        query_vec = self.combined_model.encode(input_text)

        similarities = [
            cosine_similarity([query_vec], [self.combined_embeddings["embeddings"][i]])[0][0]
            for i in range(len(self.combined_embeddings["embeddings"]))
        ]

        print(f"Similarities: {similarities}")
        best_idx = int(np.argmax(similarities))
        best_score = similarities[best_idx]
        best_id = int(self.combined_embeddings["ids"][best_idx])
        best_text = self.combined_embeddings["texts"][best_idx]

        print(f"Best Score: {best_score} for '{input_text}' → Match: '{best_text}' (ID: {best_id})")

        if best_score >= threshold:
            for league in self.leagues:
                if int(league["id"]) == best_id:
                    return league
        return None
    
    def predict_entity_of_interest(self, question):
        inputs = self.entity_interest_tokenizer(question, return_tensors="pt", truncation=True, padding=True, max_length=128)
        inputs = {k: v.to(self.entity_interest_model.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.entity_interest_model(**inputs)
            pred = torch.argmax(outputs.logits, dim=1).item()
        return self.entity_interest_le.inverse_transform([pred])[0]
    
    def predict_aggregation(self, question):
        inputs = self.agg_tokenizer(question, return_tensors="pt", truncation=True, padding=True, max_length=128)
        inputs = {k: v.to(self.agg_model.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.agg_model(**inputs)
            pred = torch.argmax(outputs.logits, dim=1).item()
        return self.agg_le.inverse_transform([pred])[0]
    
    

# Flask App
app = Flask(__name__)
service = DataLoaderService()

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "ready" if service.initialized else "initializing"})

@app.route("/entity_recognition", methods=["POST"])
def entity_recognition():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Missing 'question' in request body"}), 400

    try:
        entities = service.get_entities(question)
        return jsonify({"entities": entities})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/match_league", methods=["POST"])
def match_league():
    data = request.get_json()
    query = data.get("query")
    threshold = float(data.get("threshold", 0.5))

    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        result = service.match_league_combined(query, threshold)
        return jsonify({"matched_league": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/predict_entity_of_interest", methods=["POST"])
def predict_entity():
    data = request.get_json()
    question = data.get("question")
    if not question:
        return jsonify({"error": "Missing 'question' in request body"}), 400
    try:
        result = service.predict_entity_of_interest(question)
        return jsonify({"prediction": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict_aggregation", methods=["POST"])
def predict_aggregation():
    data = request.get_json()
    question = data.get("question")
    if not question:
        return jsonify({"error": "Missing 'question' in request body"}), 400
    try:
        result = service.predict_aggregation(question)
        return jsonify({"prediction": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
