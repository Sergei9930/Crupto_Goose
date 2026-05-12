import time

from exchanges.binance_rest import get_binance_prices
from exchanges.bybit_rest import get_bybit_prices

from scanners.spread_scanner import find_spreads
from signals.signal_processor import process_signals


while True:

    print("New scan started")

    binance_data = get_binance_prices()
    bybit_data = get_bybit_prices()

    find_spreads(binance_data, bybit_data)

    process_signals()

    print("Scan finished")

    time.sleep(5)