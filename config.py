import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/covid.db")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
APP_PORT = int(os.getenv("APP_PORT", 5000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
