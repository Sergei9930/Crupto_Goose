import time
import requests


BYBIT_URL = "https://api.bybit.com/v5/market/tickers?category=spot"


def get_bybit_prices(max_retries=5, timeout=10):
    """Fetch and normalize Bybit spot tickers with retry/backoff."""
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(BYBIT_URL, timeout=timeout)
            response.raise_for_status()
            payload = response.json()

            tickers = payload.get("result", {}).get("list", [])

            normalized_data = []
            for item in tickers:
                symbol = (item.get("symbol") or "").upper()
                if not symbol:
                    continue

                last_price = float(item.get("lastPrice", 0) or 0)
                turnover_24h_quote = float(item.get("turnover24h", 0) or 0)

                if last_price <= 0:
                    continue

                normalized_data.append({
                    "exchange": "bybit",
                    "symbol": symbol,
                    "price": last_price,
                    "volume_24h_quote": turnover_24h_quote,
                })

            return normalized_data
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            sleep_s = min(2 ** (attempt - 1), 10)
            print(f"[BYBIT REST] retry {attempt}/{max_retries} after error: {exc}")
            time.sleep(sleep_s)

    print(f"[BYBIT REST] failed after retries: {last_error}")
    return []
