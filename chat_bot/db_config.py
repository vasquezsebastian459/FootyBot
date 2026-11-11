"""Database connection settings, read from environment variables.

Set these in a .env file at the repo root (see .env.example).
"""

import os

from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("FOOTYBOT_DB_NAME"),
    "user": os.getenv("FOOTYBOT_DB_USER"),
    "password": os.getenv("FOOTYBOT_DB_PASSWORD"),
    "host": os.getenv("FOOTYBOT_DB_HOST", "localhost"),
    "port": os.getenv("FOOTYBOT_DB_PORT", "5432"),
}
