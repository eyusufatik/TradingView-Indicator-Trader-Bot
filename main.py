from distutils.command.config import config
from binance.client import Client
from binance.helpers import round_step_size
from binance.enums import *
from binance import ThreadedWebsocketManager
from threading import Lock
from flask import Flask, request

import configs
from util_functions import get_account_worth, pretty_print, parse_webhook, get_lot_step_size, get_price_step_size, send_telegram_message

mutex = Lock()
order_id_entry_price = {}

app = Flask(__name__)
client = Client(configs.API_KEY, configs.API_SECRET)
twm = ThreadedWebsocketManager(api_key=configs.API_KEY, api_secret=configs.API_SECRET)
twm.start()

def handle_socket_message(msg):
    if msg["e"] == "executionReport":
        if msg["S"] == "BUY" and msg["x"] == "TRADE":
            if msg["z"] == msg["Q"]: # cumulative filled quantity == order quantity?
                mutex.acquire()
                symbol = msg["s"]
                buy_price = order_id_entry_price[msg["i"]]
                size = float(msg["Q"])*buy_price
                send_telegram_message(f"Buy order filled: {symbol} @{buy_price} size: ${size}")
                sell_price = round_step_size(buy_price * 1,29, get_price_step_size(symbol))
                try:
                    client.order_limit_sell(symbol=symbol, quantity=msg["z"], price=sell_price)
                except Exception as e:
                    send_telegram_message(f"Exception in bot:\n{e.message}")
                    print(e.message)
                else:
                    size = float(msg["z"]) * sell_price
                    send_telegram_message(f"Sent sell order: {symbol} @{sell_price} size: ${size}")
                mutex.release()
        elif msg["S"] == "SELL" and msg["x"] == "TRADE":
            pass

twm.start_user_socket(callback=handle_socket_message)    


@app.route("/hello", methods=["GET"])
def hello_world():
    send_telegram_message("hellllllloooooo")
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
        free_usdt = float(client.get_asset_balance(asset="USDT")["free"])
        if free_usdt >= account_worth / 10:
            current_price = float(client.get_symbol_ticker(symbol=ticker)["price"])
            order_price = round_step_size(
                current_price * 0.99, get_price_step_size(ticker))
            order_amount = round_step_size(
                (free_usdt)/order_price, get_lot_step_size(ticker))
            new_order = None
            mutex.acquire()
            try:
                new_order = client.order_limit_buy(symbol=ticker, quantity=order_amount, price=order_price)
            except Exception as e:
                send_telegram_message(f"Exception in bot:\n{e.message}")
                print(e.message)
            else:
                order_id_entry_price[new_order["orderId"]] = order_price
                send_telegram_message(f"Sent buy order: {ticker} @{order_price} size: ${order_amount*order_price}")
            mutex.release()
    elif side == "SELL":
        open_orders_on_ticker = client.get_open_orders(symbol=ticker)

        if len(open_orders_on_ticker) > 0:
            for order in open_orders_on_ticker:
                orderId = order["orderId"]
                mutex.acquire()
                try:
                    client.cancel_order(symbol=ticker, orderId=orderId)
                except Exception as e:
                    send_telegram_message(f"Exception in bot:\n{e.message}")
                    print(e.message)
                else:
                    order_side = order["side"]
                    send_telegram_message(f"Cancelled {order_side} order for {ticker} due to sell signal.")
                mutex.release()
        
        mutex.acquire()
        asset_amount = float(client.get_asset_balance(asset=ticker.strip("USDT")["free"]))
        if asset_amount > 0:
            order_price = float(client.get_symbol_ticker(symbol=ticker)["price"])
            try:
                client.order_limit_sell(symbol=ticker, quantity=asset_amount, price=order_price)
            except Exception as e:
                send_telegram_message(f"Exception in bot:\n{e.message}")
                print(e.message)
            else:
                send_telegram_message(f"Sent sell order: {ticker} @{order_price} size: ${asset_amount*order_price}")
        mutex.release()
        return {"msg": "Thx."}, 200

    return {"msg": "Not implemented yet."}, 400
