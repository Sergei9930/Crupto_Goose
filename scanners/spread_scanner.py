from signals.signal_queue import add_signal
from signals.signal_tracker import track_signal


MIN_VOLUME_24H = 500_000
MIN_SPREAD_PCT = 0.5
MAX_SPREAD_PCT = 5


def find_spreads(binance_data, bybit_data):
    print("Scanner started")

    excluded_words = ["3L", "3S", "5L", "5S", "BULL", "BEAR", "UP", "DOWN"]
    excluded_symbols = ["USDT", "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "DAIUSDT"]

    bybit_map = {item["symbol"]: item for item in bybit_data}

    for binance_item in binance_data:
        symbol = binance_item["symbol"]

        if not symbol.endswith("USDT"):
            continue
        if symbol in excluded_symbols:
            continue
        if any(word in symbol for word in excluded_words):
            continue

        bybit_item = bybit_map.get(symbol)
        if not bybit_item:
            continue

        binance_price = float(binance_item.get("price", 0) or 0)
        bybit_price = float(bybit_item.get("price", 0) or 0)

        if bybit_price <= 0 or binance_price <= 0:
            continue

        spread = abs((binance_price - bybit_price) / bybit_price) * 100

        binance_volume_24h = float(binance_item.get("volume_24h_quote", 0) or 0)
        bybit_volume_24h = float(bybit_item.get("volume_24h_quote", 0) or 0)

        if (
            MIN_SPREAD_PCT < spread < MAX_SPREAD_PCT
            and binance_volume_24h > MIN_VOLUME_24H
            and bybit_volume_24h > MIN_VOLUME_24H
        ):
            signal_count = track_signal(symbol)
            if signal_count < 3:
                continue

            add_signal(
                symbol=symbol,
                spread=spread,
                binance_price=binance_price,
                bybit_price=bybit_price,
                binance_volume_24h=binance_volume_24h,
                bybit_volume_24h=bybit_volume_24h,
            )

            print("==========")
            print("CONFIRMED SIGNAL")
            print("Symbol:", symbol)
            print("Binance price:", binance_price)
            print("Bybit price:", bybit_price)
            print("Spread:", round(spread, 2), "%")
            print("Signal confirmations:", signal_count)
