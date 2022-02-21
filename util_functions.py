import json
import math
from flask_restful import reqparse
from binance.client import Client
import telebot

import configs

client = Client(configs.API_KEY, configs.API_SECRET)

bot = telebot.TeleBot(configs.TELEGRAM_TOKEN)


symbol_infos = {}


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
            if asset != "USDT":
                price = float(client.get_symbol_ticker(
                    symbol=asset+"USDT")["price"])
                sum += price * total
            else:
                sum += total

    return sum


def round_down_step_size(number, step_size):
    precision = int(round(-math.log(step_size, 10), 0))
    factor = math.pow(10, precision)
    return math.floor(number * factor)/factor

def get_lot_step_size(symbol: str):
    symbol_info = symbol_infos.get(symbol)

    if symbol_info is None:
        symbol_info = client.get_symbol_info(symbol)
        symbol_infos[symbol] = symbol_info
    
    return float(symbol_info["filters"][2]["stepSize"])


def get_price_step_size(symbol: str):
    symbol_info = symbol_infos.get(symbol)

    if symbol_info is None:
        symbol_info = client.get_symbol_info(symbol)
        symbol_infos[symbol] = symbol_info
    
    return float(symbol_info["filters"][0]["tickSize"])


def send_telegram_message(msg: str):
    bot.send_message(-725645043, msg)
