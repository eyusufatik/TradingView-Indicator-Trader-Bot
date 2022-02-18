import json
from flask_restful import reqparse

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
