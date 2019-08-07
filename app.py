"""
Usage: app.py (-a | -o -i <integer> | -t | --inspect)

Dashboard API for crypto currency

Arguments:
    -a              Run API
    -o              Run OHLC websocket
    -i <int>        OHLC interval in minutes
    -t              Run ticker websocket
    -h              Help
    --inspect       Run inspector on ticker data
"""

import os
import sys
from time import sleep

from flask_api import FlaskAPI
from flask_cors import CORS

from config import app_config
from log import log
from docopt import docopt

config_name: str = os.getenv("APP_SETTINGS")

if config_name is None:
    log.error("Missing APP_SETTINGS= environment variable.")
    sys.exit(0)

if os.getenv("DATABASE_URL") is None:
    log.error("Missing DATABASE_URL= environment variable.")
    sys.exit(0)


def create_app() -> FlaskAPI:

    app: FlaskAPI = FlaskAPI(__name__)
    app.config.from_object(app_config[config_name])
    app.config['ENV'] = config_name

    return app


app = create_app()
app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin'
CORS(app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
    args = docopt(__doc__)

    interval: int = 1
    if args["-i"]:
        if int(args["-i"]) not in [0, 1,5,15,30,60,240]:
            log.error("Invalid ticker/OHLC interval use: 1, 5, 15, 30, 60 or 240 (0=all).")
            sys.exit(1)
        else:
            interval = int(args["-i"])

    if args["-o"]:
        from kraken_websocket import run_ohlc_websocket, kraken_rest_api_to_psql

        if interval == 0:
            log.info("Retrieving all intervals")
            for i in [1,5,15,30,60,240]:
                kraken_rest_api_to_psql(interval=i)
                log.info("...")
                sys.stdout.flush()
                sleep(2)
            sys.exit(0)

        run_ohlc_websocket(interval=interval)

    if args["-t"]:
        from kraken_websocket import run_ticker_websocket
        run_ticker_websocket()

    if args["-a"]:
        from db import db
        db.init_app(app)
        from api.account import account_bp
        from api.orders import orders

        app.register_blueprint(account_bp, url_prefix="/account")
        app.register_blueprint(orders, url_prefix="/orders")
        app.run(debug=config_name != "production")

    if args["--inspect"]:
        from kraken_inspect import run
        run()

    if not args["-a"] and not args["-t"] and not args["--inspect"]:
        print(__doc__)
