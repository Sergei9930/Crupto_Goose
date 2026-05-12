import time
import requests


BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"


def get_binance_prices(max_retries=5, timeout=10):
    """Fetch and normalize Binance spot tickers with retry/backoff."""
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(BINANCE_URL, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            normalized_data = []
            for item in data:
                symbol = item.get("symbol")
                if not symbol:
                    continue

                last_price = float(item.get("lastPrice", 0) or 0)
                quote_volume_24h = float(item.get("quoteVolume", 0) or 0)

                if last_price <= 0:
                    continue

                normalized_data.append({
                    "exchange": "binance",
                    "symbol": symbol.upper(),
                    "price": last_price,
                    "volume_24h_quote": quote_volume_24h,
                })

            return normalized_data
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            sleep_s = min(2 ** (attempt - 1), 10)
            print(f"[BINANCE REST] retry {attempt}/{max_retries} after error: {exc}")
            time.sleep(sleep_s)

    print(f"[BINANCE REST] failed after retries: {last_error}")
    return []
