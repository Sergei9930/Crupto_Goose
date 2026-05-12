import requests


def get_binance_prices():

    url = "https://api.binance.com/api/v3/ticker/24hr"

    response = requests.get(url)

    data = response.json()

    normalized_data = []

    for item in data:

        normalized_item = {
            "exchange": "binance",
            "symbol": item["symbol"],
            "price": float(item["lastPrice"]),
"volume": float(item["quoteVolume"])
        }

        normalized_data.append(normalized_item)

    return normalized_data