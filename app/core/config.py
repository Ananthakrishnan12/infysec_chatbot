import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
