from binance.client import Client
from binance import ThreadedWebsocketManager
from binance.helpers import round_step_size

from util_functions import round_down_step_size, get_lot_step_size, get_price_step_size, send_telegram_message
import configs

client = Client(configs.API_KEY, configs.API_SECRET)
twm = ThreadedWebsocketManager(
        api_key=configs.API_KEY, api_secret=configs.API_SECRET)

def handle_socket_message(msg):
    if msg["e"] == "executionReport" and msg["x"] == "TRADE" and msg["z"] == msg["q"]:
        if msg["S"] == "BUY":
            symbol = msg["s"]
            buy_price = round_step_size(float(msg["Z"]) / float(msg["z"]), get_price_step_size(symbol))
            size = round_step_size(float(msg["q"])*buy_price, get_price_step_size(symbol))
            send_telegram_message(
                f"Buy order filled: {symbol} @{buy_price} size: ${size}")
            sell_price = round_step_size(
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
                    f"Sent sell order: {symbol} @{sell_price} size: ${size:.2f}")
        elif msg["S"] == "SELL":
            symbol = msg["s"]
            sell_price = round_step_size(float(msg["Z"]) / float(msg["z"]), get_price_step_size(symbol))
            size = round_step_size(float(msg["q"])*sell_price, get_price_step_size(symbol))
            send_telegram_message(
                f"Sell order filled: {symbol} @{sell_price} size: ${size}")

if __name__ == "__main__":
    twm.setDaemon(True)
    twm.start()
    twm.start_user_socket(callback=handle_socket_message)
    twm.join()