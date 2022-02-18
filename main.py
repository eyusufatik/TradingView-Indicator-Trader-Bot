from distutils.command.config import config
from binance.client import Client
from flask import Flask, request

import configs
from util_functions import get_account_worth, pretty_print, parse_webhook

app = Flask(__name__)
client = Client(configs.API_KEY, configs.API_SECRET)


@app.route("/hello", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/webhook", methods=["POST"])
def tradingview_hook():
    args = parse_webhook(request)
    passphrase = args["passphrase"]
    time_str = args["time"]
    side = args["side"]
    ticker = args["ticker"]
    bar = args["bar"]

    if passphrase != configs.TV_PASS:
        return {"msg": "wrong passphrase"}, 400

    if side == "BUY":
        account_worth = get_account_worth()
        free_usdt = client.get_asset_balance(asset="USDT")
        if free_usdt >= account_worth / 10:
            ticker_price = client.get_symbol_ticker(symbol=ticker)["price"]
            order_price = ticker_price * 0.99
            order_amount = account_worth / 10
            new_order = client.order_limit_buy(symbol=ticker, )
    else:
        return None

    return None
    
