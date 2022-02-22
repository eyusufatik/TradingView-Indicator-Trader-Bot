from binance.client import Client
#from binance.helpers import round_step_size
from binance.enums import *
from binance import ThreadedWebsocketManager
from threading import Lock
from flask import Flask, request
import os

import configs
from util_functions import get_account_worth, parse_webhook, get_lot_step_size, get_price_step_size, send_telegram_message, round_down_step_size

mutex = Lock()

app = Flask(__name__)
client = Client(configs.API_KEY, configs.API_SECRET)
twm = ThreadedWebsocketManager(
        api_key=configs.API_KEY, api_secret=configs.API_SECRET)


def handle_socket_message(msg):
    if msg["e"] == "executionReport" and msg["x"] == "TRADE" and msg["z"] == msg["q"]:
        mutex.acquire()
        if msg["S"] == "BUY":
            symbol = msg["s"]
            buy_price = float(msg["Z"]) / float(msg["z"])
            size = float(msg["q"])*buy_price
            send_telegram_message(
                f"Buy order filled: {symbol} @{buy_price:.2f} size: ${size:.2f}")
            sell_price = round_down_step_size(
                buy_price * configs.SELL_UP, get_price_step_size(symbol))
            try:
                quantity = float(client.get_asset_balance(
                    asset=msg["s"].removesuffix("USDT"))["free"])
                if quantity > 0:
                    quantity = round_down_step_size(
                        quantity, get_lot_step_size(msg["s"]))
                    client.order_limit_sell(
                        symbol=symbol, quantity=quantity, price=sell_price)
            except Exception as e:
                send_telegram_message(f"Exception in bot:\n{e.message}")
                print(e.message)
            else:
                size = float(msg["z"]) * sell_price
                send_telegram_message(
                    f"Sent sell order: {symbol} @{sell_price:.2f} size: ${size:.2f}")
        elif msg["S"] == "SELL":
            symbol = msg["s"]
            sell_price = float(msg["Z"]) / float(msg["z"])
            size = float(msg["q"])*sell_price
            send_telegram_message(
                f"Sell order filled: {symbol} @{sell_price:.2f} size: ${size:.2f}")
        mutex.release()


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

    if not twm.is_alive():
        twm.start()
        twm.start_user_socket(callback=handle_socket_message)

    if side == "BUY":
        account_worth = get_account_worth()
        free_usdt = float(client.get_asset_balance(asset="USDT")["free"])
        if free_usdt >= account_worth / configs.POS_DIVIDER:
            # current_price = float(
            #     client.get_symbol_ticker(symbol=ticker)["price"])
            current_price = float(bar["close"])
            order_price = round_down_step_size(
                current_price * configs.BUY_DOWN, get_price_step_size(ticker))  # current_price * 0,99
            order_amount = round_down_step_size(
                (account_worth/configs.POS_DIVIDER)/order_price, get_lot_step_size(ticker))
            if order_amount > 0:
                mutex.acquire()
                try:
                    client.order_limit_buy(
                        symbol=ticker, quantity=order_amount, price=order_price)
                except Exception as e:
                    send_telegram_message(f"Exception in bot:\n{e.message}")
                    print(e.message)
                else:
                    send_telegram_message(
                        f"Sent buy order: {ticker} @{order_price:.2f} size: ${(order_amount*order_price):.2f}")
                mutex.release()
    elif side == "SELL":
        open_orders_on_ticker = client.get_open_orders(symbol=ticker)

        mutex.acquire()
        for order in open_orders_on_ticker:
            orderId = order["orderId"]
            try:
                client.cancel_order(symbol=ticker, orderId=orderId)
            except Exception as e:
                send_telegram_message(f"Exception in bot:\n{e.message}")
                print(e.message)
            else:
                order_side = order["side"]
                send_telegram_message(
                    f"Cancelled {order_side} order for {ticker} due to sell signal.")

        asset_amount = round_down_step_size(float(client.get_asset_balance(
            asset=ticker.removesuffix("USDT"))["free"]), get_lot_step_size(ticker))
        if asset_amount > 0:
            order_price = round_down_step_size(float(client.get_symbol_ticker(
                symbol=ticker)["price"]), get_price_step_size(ticker))
            try:
                client.order_limit_sell(
                    symbol=ticker, quantity=asset_amount, price=order_price)
            except Exception as e:
                send_telegram_message(f"Exception in bot:\n{e.message}")
                print(e.message)
            else:
                send_telegram_message(
                    f"Sent sell order: {ticker} @{order_price:.2f} size: ${(asset_amount*order_price):.2f}")
        mutex.release()
    return {"msg": "Thx."}, 200
