"""
Usage: app.py [-a]  [(-o -i <integer>)] [-t] | --inspect

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

from flask import request, jsonify, render_template
from flask_api import FlaskAPI
from flask_cors import CORS, cross_origin

from config import app_config

from log import log
from docopt import docopt

import threading

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
cors = CORS(app, resources={r"*": {"origins": "*"}})

def main():

    from portfolio import Portfolio

    args = docopt(__doc__)

    if args["-i"]:
        intervals = list()
        for i in args["-i"].split(","):
            try:
                intervals.append(int(i))
            except Exception as e:
                log.error("Could not interpret intervals, use comma-seperated list.")
                sys.exit(1)

            if int(i) not in [0, 1,5,15,30,60,240]:
                log.error("Invalid ticker/OHLC interval use: 1, 5, 15, 30, 60 or 240.")
                sys.exit(1)

        if args["-o"]:
            from kraken_websocket import run_ohlc_websocket, kraken_rest_api_to_psql

            if intervals == 0:
                log.info("Retrieving all intervals")
                for i in [1,5,15,30,60,240]:
                    kraken_rest_api_to_psql(interval=i)
                    log.info("...")
                    sys.stdout.flush()
                    sleep(2)
                sys.exit(0)

        threads = list()
        for i in intervals:
            threads.append(threading.Thread(target=run_ohlc_websocket, args=(i,)))

        for t in threads:
            t.start()

    if args["-a"]:
        from db import db
        db.init_app(app)
        from api.account import account_bp
        from api.orders import orders
        from api.ohlc import ohlc_bp

        @app.route("/login", methods=['GET', 'POST', 'OPTIONS'])
        @cross_origin(allow_headers=['Content-Type'])
        def login() -> dict:
            from auth import LoginManager
            login_manager = LoginManager()
            return login_manager.login()

            #  select t.token, u.name from tokens as t
            #  join users as u on user_id = u.id
            #  where u.name = 'banana'
            #  order by timestamp desc
            #  limit 1;
            return jsonify({"token": "9b6e1d23-a656-4118-9037-ebf288536ad5"})

        app.register_blueprint(account_bp, url_prefix="/account")
        app.register_blueprint(orders, url_prefix="/orders")
        app.register_blueprint(ohlc_bp, url_prefix="/graph")
        app.run(debug=config_name != "production")

    if args["-t"]:

        from kraken_websocket import run_ticker_websocket
        portfolio = Portfolio()

        thread = threading.Thread(target=run_ticker_websocket, args=(portfolio,))
        thread.start()

    if args["--inspect"]:
        from kraken_inspect import run
        run()

    if not args["-a"] and not args["-t"] and not args["--inspect"] and not args["-o"]:
        print(__doc__)

if __name__ == "__main__":
    main()
