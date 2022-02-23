import os
import redis

from dotenv import load_dotenv


load_dotenv()

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
TV_PASS = os.environ.get("TV_PASS")
DEBUG = os.environ.get("DEBUG") == "1"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
BUY_DOWN = float(os.environ.get("BUY_DOWN"))
SELL_UP = float(os.environ.get("SELL_UP"))
POS_DIVIDER = float(os.environ.get("POS_DIVIDER"))
REDIS_URL = os.environ.get("REDIS_URL")

redis = redis.from_url(REDIS_URL)

x = redis.get("BUY_DOWN")
if not x is None:
    BUY_DOWN = float(x)

x = redis.get("SELL_UP")
if not x is None:
    SELL_UP = float(x)

redis.close()