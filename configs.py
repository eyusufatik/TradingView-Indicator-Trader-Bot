import os


from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
