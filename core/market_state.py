market_state = {}


def update_market_state(symbol, exchange, data):
    if symbol not in market_state:
        market_state[symbol] = {}

    market_state[symbol][exchange] = data


def get_market_state():
    return market_state