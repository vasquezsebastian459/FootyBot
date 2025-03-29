from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from print_colors import print_colored,print_colored_full_line

import traceback
from run_query import init_connection_pool, close_connection_pool
import threading
import time
import psutil

import os
from run_chatbot import Chatbot


app = Flask(__name__)
CORS(app)  # Enable CORS

chatbot = Chatbot()


# Adjust the root path for static files
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('webpage/images', filename)

@app.route('/chat', methods=['POST'])
def chat():
    
    data = request.get_json()
    user_question = data['message']
    context = data['context']


    try:
        output = chatbot.run(user_question, context)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        output = {
            'response': "Sorry, I encountered an error. Please try again later.",
            'keyinfo_context': context,
            'links_info': {}
        }


    # Get Overall Time
    end_time = time.time()
    overall_time = end_time - chatbot.performance.start_overall_time
    print(f"Overall Time: {overall_time}")

    return jsonify(output)


@app.route('/')
def serve_html():
    return send_from_directory('.', 'webpage/index2.html') 

if __name__ == '__main__':
    init_connection_pool()
    chatbot.load_data()
    
    app.run(debug=False, host="0.0.0.0", port=9876)

    close_connection_pool()
