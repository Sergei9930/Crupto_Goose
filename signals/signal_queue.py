import time

signal_queue = {}

MAX_SIGNAL_LIFETIME = 60
COOLDOWN_TIME = 20


def add_signal(symbol, spread, binance_price, bybit_price, binance_volume_24h, bybit_volume_24h):
    current_time = time.time()

    payload = {
        "spread": spread,
        "status": "new",
        "created_at": current_time,
        "last_seen": current_time,
        "last_processed": 0,
        "binance_price": binance_price,
        "bybit_price": bybit_price,
        "binance_volume_24h": binance_volume_24h,
        "bybit_volume_24h": bybit_volume_24h,
    }

    if symbol not in signal_queue:
        signal_queue[symbol] = payload
        print(f"[QUEUE] Добавлен сигнал: {symbol}")
    else:
        signal_queue[symbol].update(payload)


def get_signals():
    return signal_queue


def cleanup_signals():
    current_time = time.time()
    to_delete = []

    for symbol, data in signal_queue.items():
        if current_time - data["last_seen"] > MAX_SIGNAL_LIFETIME:
            to_delete.append(symbol)

    for symbol in to_delete:
        del signal_queue[symbol]
        print(f"[QUEUE] Удалён старый сигнал: {symbol}")
