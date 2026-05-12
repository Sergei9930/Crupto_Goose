import requests


def get_bybit_prices():

    url = "https://api.bybit.com/v5/market/tickers?category=spot"

    response = requests.get(url)

    data = response.json()

    normalized_data = []

    for item in data["result"]["list"]:

        normalized_item = {
    "exchange": "bybit",
    "symbol": item["symbol"],
    "price": float(item["lastPrice"]),
    "volume": float(item["turnover24h"])
}
        normalized_data.append(normalized_item)

    return normalized_data