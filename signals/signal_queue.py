import time

signal_queue = {}

MAX_SIGNAL_LIFETIME = 30   # сколько живёт сигнал без обновления
COOLDOWN_TIME = 20         # пауза между обработками


def add_signal(symbol, spread):

    current_time = time.time()

    if symbol not in signal_queue:
        signal_queue[symbol] = {
            "spread": spread,
            "status": "new",
            "created_at": current_time,
            "last_seen": current_time,
            "last_processed": 0
        }

        print(f"[QUEUE] Добавлен сигнал: {symbol}")

    else:
        signal_queue[symbol]["spread"] = spread
        signal_queue[symbol]["last_seen"] = current_time


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