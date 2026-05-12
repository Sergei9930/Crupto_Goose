from signals.signal_queue import add_signal
from signals.signal_tracker import track_signal


def find_spreads(binance_data, bybit_data):

    print("Scanner started")

    excluded_words = [
        "3L",
        "3S",
        "5L",
        "5S",
        "BULL",
        "BEAR",
        "UP",
        "DOWN"
    ]

    excluded_symbols = [
        "USDT",
        "USDCUSDT",
        "FDUSDUSDT",
        "TUSDUSDT",
        "DAIUSDT"
    ]

    for binance_item in binance_data:

        for bybit_item in bybit_data:

            if (
                binance_item["symbol"] == bybit_item["symbol"]
                and binance_item["symbol"].endswith("USDT")
            ):

                if binance_item["symbol"] in excluded_symbols:
                    continue

                if any(
                    word in binance_item["symbol"]
                    for word in excluded_words
                ):
                    continue

                binance_price = binance_item["price"]

                bybit_price = bybit_item["price"]

                spread = abs(
                    (binance_price - bybit_price)
                    / bybit_price
                ) * 100

                if (
                    spread > 0.5
                    and spread < 5
                    and binance_item["volume"] > 100000
                    and bybit_item["volume"] > 100000
                ):

                    signal_count = track_signal(
                        binance_item["symbol"]
                    )

                    if signal_count < 3:
                        continue
                    add_signal(
                    binance_item["symbol"],
                                 spread
                     )

                    print("==========")
                    
  
                    print("CONFIRMED SIGNAL")

                    print("Symbol:", binance_item["symbol"])

                    print("Binance price:", binance_price)

                    print("Bybit price:", bybit_price)

                    print("Spread:", round(spread, 2), "%")

                    print(
                        "Signal confirmations:",
                        signal_count
                    )