import os


from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
TV_PASS = os.environ.get("TV_PASS")
DEBUG = os.environ.get("DEBUG") == "1"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")