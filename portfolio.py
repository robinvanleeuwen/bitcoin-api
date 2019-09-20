from pprint import pprint
from setup import get_kraken_api
from log import log

class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Portfolio(metaclass=Singleton):

    def __init__(self, base_currency = "EUR"):

        self._api = get_kraken_api()
        self.base = base_currency
        self.assets = list()
        self.amounts = dict()
        self.prices = dict()

        self.update_assets()
        self.update_price()

    def update_assets(self):
        log.debug("Update Assets")
        balance = self._api.query_private("Balance")

        for asset in balance["result"].items():
            self.amounts[asset[0][1:]] = float(asset[1])
            if asset[0][0] == "Z": self.base = asset[0][1:]
            if asset[0][0] == "X": self.assets.append(asset[0][1:])

    def update_price(self):
        log.debug("Update Price")
        if len(self.assets) == 0:
            self.update_assets()

        pairs = [f"X{a}Z{self.base}" for a in self.assets]

        for p in pairs:
            ticker = self._api.query_public('Ticker', {'pair': p})
            self.prices[p[1:4]] = float(ticker["result"][p]["c"][0])


    def trades_history(self, type=None):
        result = self._api.query_private('TradesHistory')

        trades = result["result"]["trades"]

        fee: float = 0.0
        for trade in trades.values():
            fee += float(trade["fee"])
        print(fee)
        return trades

    def price_history(self, pair=None):
        pass

    @property
    def asset_amounts(self):
        return {x:self.amounts[x] for x in self.assets}

    @property
    def asset_value(self):
        values = dict()

        for x in self.assets:
            values[x] = self.prices[x] * self.amounts[x]

        return values

    @property
    def base_value(self):
        return self.amounts[self.base]


    @property
    def pairs(self):
        return [f"{x}/{self.base}" for x in self.assets]

    @property
    def total_value(self):
        return {self.base: sum(self.asset_value.values()) + self.base_value}

    def get_summary(self, update_assets=False):

        if update_assets: self.update_assets()

        self.update_price()

        summary = dict()
        summary["assets"] = {x: dict() for x in self.assets}
        for x in summary["assets"].keys():
            summary["assets"][x] = {
                "amount": round(self.asset_amounts[x],6),
                "value": round(self.asset_value[x], 6)
            }

        summary["base_asset"] = self.base
        summary["base_amount"] = round(self.amounts[self.base],6)
        summary["total_value"] = round(sum(self.asset_value.values()) + self.base_value,6)

        return summary

    def __str__(self):
        return str(self.get_summary())


if __name__ == "__main__":
    p = Portfolio()
    pprint(p.get_summary())
    print(p)

