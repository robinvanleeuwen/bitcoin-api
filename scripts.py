import logging
import sys

import requests

from datetime import datetime

from app import app, db

logging.basicConfig()
logging.getLogger(__name__).setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

log.debug("Retrieving rates.")


def get_kraken_ohlc(interval=1, since=0, pair="XXBTZEUR"):
    data = dict()

    if since != 0:
        data["since"] = since
    if interval != 0:
        data["interval"] = interval
    data["pair"] = pair


    response = requests.post(data=data, url=url)

    return response.json()


def get_last_ohlc_timestamp(interval: int):

    last_open_ohlc = (
        db.session.query(OhlcXXBTZEUR)
        .filter(OhlcXXBTZEUR.interval == interval)
        .order_by(OhlcXXBTZEUR.timestamp.desc())
        .first()
    )

    return last_open_ohlc


def fill_interval(interval=1, pair="XXBTZEUR"):

    last_record = get_last_ohlc_timestamp(interval=interval)
    if last_record is not None:
        since = last_record.unixtime
    else:
        since = 0

    data = get_kraken_ohlc(since=since, interval=interval, pair=pair)
    log.debug(f'Got {len(data["result"][pair])} records')
    for record in data["result"][pair]:

        r = OhlcXXBTZEUR()
        r.interval = interval
        r.unixtime = record[0]
        r.timestamp = datetime.fromtimestamp(record[0])
        r.open = record[1]
        r.high = record[2]
        r.low = record[3]
        r.close = record[4]
        r.vwap = record[5]
        r.count = record[6]

        # If the kraken record matches the last record
        # in the database, replace the one in the db

        if last_record is not None and r.unixtime == last_record.unixtime:
            log.debug(f"Removing record w timestamp: {last_record.timestamp}")
            db.session.delete(last_record)
            db.session.commit()

        log.debug(f"Adding record for timestamp: {r.timestamp} close: {r.close}")

        db.session.add(r)
        db.session.commit()


with app.app_context():

    try:
        interval = sys.argv[1]
    except IndexError:
        interval = 1

    db.init_app(app)

    kraken_rest_api_to_psql(interval)

    fill_interval(interval)
