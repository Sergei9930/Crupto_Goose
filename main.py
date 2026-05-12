import time

from exchanges.binance_rest import get_binance_prices
from exchanges.bybit_rest import get_bybit_prices
from scanners.spread_scanner import find_spreads
from signals.signal_processor import process_signals
from ws.pipeline import run_ws_followup_for_active_signals

SCAN_INTERVAL_SECONDS = 3


def run_loop():
    while True:
        print("New scan started")

        binance_data = get_binance_prices()
        bybit_data = get_bybit_prices()

        find_spreads(binance_data, bybit_data)
        run_ws_followup_for_active_signals(sample_seconds=8)
        process_signals()

        print("Scan finished")
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_loop()
