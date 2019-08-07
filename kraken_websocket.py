import datetime
import sys

import requests
from kraken_wsclient_py import kraken_wsclient_py as kraken_client
from sqlalchemy import and_, exists
from sqlalchemy.orm import Session

from log import log
from db import db
from db.models import Ticker, Ohlc

subscriptions: dict = dict()


def kraken_rest_api_to_psql(interval=1, pair="XXBTZEUR"):

    log.info(
        f"Retrieving past data for {pair} with interval {interval} from kraken REST Api"
    )

    url: str = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"

    data: dict = dict()
    data["interval"] = interval
    data["pair"] = pair

    result: dict = requests.post(data=data, url=url).json()

    num_kraken_records: int = len(result["result"][pair])

    log.info(f"Got {num_kraken_records} records")

    session: Session = db.session()
    c: int = 0
    for record in result["result"][pair]:

        existing_record = session.query(
            exists().where(
                and_(
                    Ohlc.begintime == record[0],
                    Ohlc.interval == interval
                ))
        ).scalar()

        if not existing_record:

            r = Ohlc()
            r.interval = interval
            r.pair = "XBT/EUR"
            r.begintime = record[0]
            r.endtime = float(record[0]) + (interval * 60.0)
            r.open = record[1]
            r.high = record[2]
            r.low = record[3]
            r.close = record[4]
            r.vwap = record[5]
            r.count = record[6]

            try:
                db.session().add(r)
                db.session.commit()

            except Exception as e:
                log.warning(f"Failure inserting record: {e}")
        else:
            c += 1

    log.info(f"{c} record(s) skipped, {num_kraken_records - c} record(s) added.")
    log.info("Done.")


def store2psql(data):

    if type(data) is list:
        handler: callable = getattr(
            sys.modules[__name__],
            f"handle_{subscriptions[data[0]]['meta']['name']}_data",
        )
        handler(data, **{"channelId": data[0]})

    if type(data) is dict and data.get("event", "") == "systemStatus":
        log.info("------------------------------------------------------")
        log.info(f"Connection ID       = {data.get('connectionID')}")
        log.info(f"System Status       = {data.get('status')}")
        log.info(f"System Version      = {data.get('version')}")
        log.info("------------------------------------------------------")

    if type(data) is dict and data.get("event", "") == "subscriptionStatus":
        log.info(f"Channel ID          = {data.get('channelID')}")
        log.info(f"Channel Name        = {data.get('subscription').get('name')}")
        log.info(f"Subscription Pair   = {data.get('pair')}")
        log.info(f"Subscription Status = {data.get('status')}")
        if data.get("status") == "error":
            log.error(f"Error message      = {data.get('errorMessage')}")

        log.info("------------------------------------------------------")

        subscriptions[data.get("channelID")] = {
            "meta": data.get("subscription"),
            "pair": data.get("pair"),
        }

    if type(data) is dict and data.get("event") == "heartbeat":
        print("\u2665", end="")
        sys.stdout.flush()


def handle_ticker_data(data, **kwargs):

    record = Ticker()

    record.a_price = data[1]["a"][0]
    record.a_whole_lot_volume = data[1]["a"][1]
    record.a_lot_volume = data[1]["a"][2]

    record.b_price = data[1]["b"][0]
    record.b_whole_lot_volume = data[1]["b"][1]
    record.b_lot_volume = data[1]["b"][2]

    record.c_price = data[1]["c"][0]
    record.c_lot_volume = data[1]["c"][1]

    record.v_today = data[1]["v"][0]
    record.v_24_hours = data[1]["v"][1]

    record.p_today = data[1]["p"][0]
    record.p_24_hours = data[1]["p"][1]

    record.t_today = data[1]["t"][0]
    record.t_24_hours = data[1]["t"][1]

    record.l_today = data[1]["l"][0]
    record.l_24_hours = data[1]["l"][1]

    record.o_today = data[1]["o"][0]
    record.o_24_hours = data[1]["o"][1]

    record.pair = data[3]

    record.timestamp = datetime.datetime.now().timestamp()
    try:
        db.session().add(record)
        db.session().commit()
        print("⇩", end="")
        sys.stdout.flush()
    except Exception as e:
        log.error(f"Could not insert ticker data: {str(e)}")



def handle_ohlc_data(data, **kwargs):

    # The Ohlc socket feeds us with updates of the given
    # interval. If the windows is new, there is no record
    # with an identical endtime, so we should insert.
    # If there is a record with identical endtime, we should
    # update the record, and we discard the trades of that
    # window-interval (1m, 5m, 30m, 60m, ...)

    def getExistingOhlcEntry(pair, endtime, interval):
        return (
            db.session()
            .query(Ohlc)
            .filter(
                and_(
                    Ohlc.pair == pair,
                    Ohlc.endtime == endtime,
                    Ohlc.interval == interval,
                )
            )
            .order_by(Ohlc.time.desc())
            .first()
        )

    interval = int(subscriptions[kwargs["channelId"]]["meta"]["interval"])
    pair = subscriptions[kwargs["channelId"]]["pair"]

    record = getExistingOhlcEntry(pair, data[1][1], interval)

    try:
        if record:
            record.time = data[1][0]
            record.begintime = float(data[1][1]) - (interval * 60.0)
            record.endtime = data[1][1]
            record.open = data[1][2]
            record.high = data[1][3]
            record.low = data[1][4]
            record.close = data[1][5]
            record.vwap = data[1][6]
            record.volume = data[1][7]
            record.count = data[1][8]

            print("↺", end="")
            sys.stdout.flush()

        else:

            record = Ohlc()
            record.pair = data[3]
            record.interval = interval
            record.pair = pair
            record.time = data[1][0]
            record.endtime = data[1][1]
            record.open = data[1][2]
            record.high = data[1][3]
            record.low = data[1][4]
            record.close = data[1][5]
            record.vwap = data[1][6]
            record.volume = data[1][7]
            record.count = data[1][8]

            print("⇩", end="")
            sys.stdout.flush()

            db.session().add(record)

        db.session().commit()

    except Exception as e:
        print(f"Failure adding/updating ohcl: {e}")


def run_ohlc_websocket(interval: int=0, pair: str= "XBT/EUR"):

    if interval == 0:
        log.warning("No interval window given, using 1 minute")
        interval = 1

    kraken_rest_api_to_psql(interval=interval)

    log.info(f"Setting up OHLC websocket")
    client = kraken_client.WssClient()
    client.subscribe_public(
        subscription={"name": "ohlc", "interval": interval}, pair=[pair], callback=store2psql
    )

    log.info("⇩ = Insert new OHLC record for this interval window.")
    log.info("↺ = Update existing record for this interval window.")
    log.info("♥ = Websocket heartbeat.")

    log.info("Starting websocket client")

    client.start()

def run_ticker_websocket(pair: str="XBT/EUR"):

    log.info(f"Setting up Ticker websocket")

    client = kraken_client.WssClient()
    client.subscribe_public(
        subscription={"name": "ticker"}, pair=[pair], callback=store2psql
    )

    log.info("Starting Ticker websocket")
    client.start()