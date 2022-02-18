from binance.client import Client
from flask import Flask, request

import configs
from util_functions import pretty_print, parse_webhook

app = Flask(__name__)
client = Client(configs.API_KEY, configs.API_SECRET)

@app.route("/webhook", methods=["POST"])
def tradingview_hook():
    args = parse_webhook(request)
    passphrase = args["passphrase"]
    time_str = args["time"]
    side = args["side"]
    ticker = args["ticker"]
    bar = args["bar"]
    

if __name__ == "__main__":
    app.run(debug=True)