import time
from decimal import Decimal as D
from db.models import Ticker
from db import db
from log import log

def get_latest_ticker(interval=0):

    if interval == 0:
        record = db.session().query(Ticker).order_by(Ticker.timestamp.desc()).limit(1).one_or_none()
        return record

    else:
        query = f"SELECT * FROM ticker WHERE to_timestamp(timestamp) > now() - interval '{interval} seconds'"
        result = db.engine.execute(query)
        data = [x for x in result]

        return data

def run():

    warn_active_interval = 20
    warn_active_min_trades = 20
    warn_active_min_diff = D(25.0)

    log.info(f"Setting up warning for active trades:")
    log.info(f"Interval  : {warn_active_interval}")
    log.info(f"Max trades: {warn_active_min_trades}")
    log.info(f"Max diff  : {warn_active_min_diff}")
    log.info("------------------------------------------")

    lws = 0.00
    while True:
        lws = warn_active_trading(
            interval=warn_active_interval,
            min_trades=warn_active_min_trades,
            min_diff=warn_active_min_diff,
            last_warning_timestamp=lws
        )
        time.sleep(1)


def warn_active_trading(
        interval: int=60,
        min_trades: int=5,
        min_diff: int=D(1.0),
        last_warning_timestamp=0.00):

    """
    Warn if rapid fluctuations in price occur.

    Shows message if in the last {interval} seconds more than {min_trades} are being
    made, with a diffence greater than {min_diff} within this time.

    :param interval:
    :param min_trades:
    :param min_diff:
    :param last_warning_timestamp:
    :return:
    """

    data = get_latest_ticker(interval)
    if len(data) < 2:
        log.debug("Tumbleweeds on tradingfloor...")
        return -1.00

    measured_diff = data[-1]['c_price'] - data[0]['c_price']

    log.debug("{a:3d} records | diff {b:10f} | interval {c:3d} | {d:19s} | {e:9f} | {f:18f} |"
        .format(
            a=len(data),
            b=measured_diff,
            c=interval,
            d=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[0]['timestamp'])),
            e=data[-1]['c_price'],
            f=data[-1]['timestamp']
        )
    )

    if len(data) >= min_trades and abs(measured_diff) > min_diff and data[-1]['timestamp'] != last_warning_timestamp:

        if measured_diff > 0:
            log.info(f"Active UP trading, diff = {measured_diff}, buy @ {data[-1]['c_price']} | {data[-1]['timestamp']}")
        if measured_diff < 0:
            log.error(f"Active DOWN trading, diff = {measured_diff} sell @ {data[-1]['c_price']} | {data[-1]['timestamp']}")

        return data[-1]["timestamp"]
