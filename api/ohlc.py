import krakenex

from flask import Blueprint
from decimal import Decimal
from auth import LoginManager
from db import db
from db.models import Ohlc
from log import log
from setup import get_kraken_api

ohlc_bp = Blueprint("ohlc_bp", __name__)

log.warning("Loading api.account")
login_manager = LoginManager()

api = get_kraken_api()

@ohlc_bp.route("ohlc/<int:ohlc_interval>", methods=["GET", "POST", "OPTIONS"])
def ohlc_data(ohlc_interval: int, limit: int = 50):
    log.debug(f"Retrieving OHLC data ({ohlc_interval} minutes interval)")
    data = [x.as_canvasjs_datapoints() for x in
        db.session()
            .query(Ohlc)
            .filter(Ohlc.interval == ohlc_interval)
            .order_by(Ohlc.endtime.desc())
            .limit(limit)
    ]
    print(data)
    return data