from crypt import methods
from binance.client import Client
from binance.enums import *
from binance.helpers import round_step_size
from threading import Lock
from flask import Flask, request
import redis

import configs
from util_functions import get_account_worth, parse_webhook, get_lot_step_size, get_price_step_size, send_telegram_message, round_down_step_size

mutex = Lock()

app = Flask(__name__)
client = Client(configs.API_KEY, configs.API_SECRET)
r = redis.from_url(configs.REDIS_URL)
p = r.pubsub()
p.subscribe("trade-multiplier-update")



@app.route("/hello", methods=["GET"])
def hello_world():
    return "Hello, World!"


@app.route("/setBuyDown", methods=["POST"])
def set_buy_down():
    args = parse_webhook(request)
    passphrase = args["passphrase"]
    buy_down = args["buyDown"]

    if passphrase != configs.TV_PASS:
        return {"msg": "wrong passphrase"}, 400
    
    if buy_down is None:
        return {"msg": "buyDown field can't be empty."}, 400
    
    configs.BUY_DOWN = buy_down
    r.set("BUY_DOWN", buy_down)
    r.publish("trade-multiplier-update", "buy-down-updated")
    
    return {"msg": "buyDown updated"}, 200


@app.route("/setSellUp", methods=["POST"])
def set_sell_up():
    args = parse_webhook(request)
    passphrase = args["passphrase"]
    sell_up = args["sellUp"]

    if passphrase != configs.TV_PASS:
        return {"msg": "wrong passphrase"}, 400

    if sell_up is None:
        return {"msg": "sellUp field can't be empty."}, 400
    
    configs.SELL_UP = sell_up
    r.set("SELL_UP", sell_up)
    r.publish("trade-multiplier-update", "sell-up-updated")
    
    return {"msg": "sellUp updated"}, 200

@app.route("/webhook", methods=["POST"])
def tradingview_hook():
    args = parse_webhook(request)
    passphrase = args["passphrase"]
    time_str = args["time"]
    side = args["side"]
    ticker = args["ticker"]
    bar = args["bar"]

    # TODO: hashed passphares implementation
    if passphrase != configs.TV_PASS:
        return {"msg": "wrong passphrase"}, 400

    # TODO: better telegram messages with formatting.
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
                try:
                    client.order_limit_buy(
                        symbol=ticker, quantity=order_amount, price=order_price)
                except Exception as e:
                    send_telegram_message(f"Exception in bot:\n{e.message}")
                    print(e.message)
                else:
                    send_telegram_message(
                        f"Sent buy order: {ticker} @{order_price} size: ${(order_amount*order_price):.2f}")
    elif side == "SELL":
        open_orders_on_ticker = client.get_open_orders(symbol=ticker)

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
            order_price = round_step_size(float(client.get_symbol_ticker(
                symbol=ticker)["price"]), get_price_step_size(ticker))
            try:
                client.order_limit_sell(
                    symbol=ticker, quantity=asset_amount, price=order_price)
            except Exception as e:
                send_telegram_message(f"Exception in bot:\n{e.message}")
                print(e.message)
            else:
                send_telegram_message(
                    f"Sent sell order: {ticker} @{order_price} size: ${(asset_amount*order_price):.2f}")
    return {"msg": "Thx."}, 200
