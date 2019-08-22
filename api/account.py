import krakenex

from flask import Blueprint
from decimal import Decimal

from auth import LoginManager
from db import db
from db.models import Ohlc
from log import log
from setup import get_kraken_api

account_bp = Blueprint("account_bp", __name__)

log.warning("Loading api.account")

login_manager = LoginManager()


def get_current_ticker_info(account: str = "kraken") -> dict:
    """
    The ticker (current price) for a specific exchange.

    :return: JSON with ticker information
    """

    if account == "kraken":

        kraken_api = krakenex.API()

        data = {"pair": ["XXBTZEUR"]}
        result = kraken_api.query_public("Ticker", data=data)
        log.debug(result)
        return {"account": account, "XXBTZEUR": result["c"][0]}

        return result

    if account == "local":
        record = (
            db.session()
            .query(Ohlc)
            .filter(Ohlc.interval == 1)
            .order_by(Ohlc.endtime.desc())
            .limit(1)
            .one_or_none()
        )

        if record:
            return {"account": account, "XXBTZEUR": record.close}
        else:
            return {"error": "no data available"}

    else:
        log.error("get_current_ticker_info(): No valid account given.")
        return {"error": "No valid account"}


@account_bp.route("/balance", methods=["GET", "POST", "OPTIONS"])
@login_manager.token_required
def api_balance():
    """
    Get the total balance and the open balance available for trading.
    :return:
    """
    api = get_kraken_api()

    if not api:
        return {"error": "Could not load Kraken API, check log."}

    log.debug("Getting account balance")
    balance = dict()
    balance["total"] = api.query_private("Balance")["result"]
    balance["total"] = correct_currency_in_dictionary(balance["total"])

    log.debug("Getting open orders")
    open_orders = api.query_private("OpenOrders")["result"]

    # Make a copy of the total dict, so we can calculate
    # the remaining balance available for trading on this
    # copy.
    balance["available"] = dict()
    balance["available"] = balance["total"].copy() # Leave total balance intact.

    log.debug("Calculating balance available for trades")
    for order_id, order in open_orders["open"].items():
        volume = Decimal(order['vol']) - Decimal(order['vol_exec'])
        log.debug(volume)

        descr = order["descr"]
        pair = descr["pair"]
        price = Decimal(descr["price"])

        base = pair[:3] if pair != "DASHEUR" else "DASH"
        quote = pair[3:] if pair != "DASHEUR" else "EUR"

        if descr["type"] == "buy":
            balance["available"][quote] -= volume * price

        if descr["type"] == "sell":
            balance["available"][base] -= volume

    return {
        "balance": balance,
        "error": ""
    }


@account_bp.route("/trades", methods=["POST", "OPTIONS"])
@login_manager.token_required
def trades():
    return {"trades": []}


def correct_currency_in_dictionary(dictionary):
    """
    Correct the currency in a dictionary to a 3 letter key.
    XXBT => XBT, ZEUR => EUR, except with DASH which stays
    the same.
    :param dictionary:
    :return: dictionary with correct keys
    """
    log.debug("Correcting currency in dictionary")
    return {key[1:]: Decimal(value) for key, value in dictionary.items() if len(key) == 4 and key != "DASH"}