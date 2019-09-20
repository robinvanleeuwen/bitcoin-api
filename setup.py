import krakenex

from log import log

def get_kraken_api():
    api = krakenex.API()
    try:
        api.load_key("/etc/kraken-api.key")
    except FileNotFoundError as e:
        log.error(f"Could not load keyfile: {e}")
        return False

    log.debug("Kraken API loaded successfully")
    return api