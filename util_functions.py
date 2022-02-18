import json
from flask_restful import reqparse
from binance.client import Client

import configs

client = Client(configs.API_KEY, configs.API_SECRET)


webhook_parser = reqparse.RequestParser()
webhook_parser.add_argument("passphrase", type=str)
webhook_parser.add_argument("time", type=str)
webhook_parser.add_argument("side", type=str)
webhook_parser.add_argument("ticker", type=str)
webhook_parser.add_argument("bar", type=dict)


def pretty_print(dic: dict):
    print(json.dumps(dic, indent=4))


def parse_webhook(req):
    return webhook_parser.parse_args(req=req)


def get_account_worth():
    sum = 0
    balances = client.get_account()["balances"]

    for balance in balances:
        asset = balance["asset"]
        free = float(balance["free"])
        locked = float(balance["locked"])
        total = free + locked

        if total > 0:
            price = float(client.get_symbol_ticker(
                symbol=asset+"USDT")["price"])
            sum += price * total

    return sum
