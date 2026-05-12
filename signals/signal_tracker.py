
import time

signal_memory = {}

DECAY_TIME = 15  # сколько сигнал живёт без обновления


def cleanup_old_signals(current_time):
    to_delete = []

    for symbol in signal_memory:
        last_seen = signal_memory[symbol]["last_seen"]

        if current_time - last_seen > DECAY_TIME:
            to_delete.append(symbol)

    for symbol in to_delete:
        del signal_memory[symbol]


def track_signal(symbol):

    current_time = time.time()

    # 🧹 сначала чистим старые сигналы
    cleanup_old_signals(current_time)

    if symbol not in signal_memory:
        signal_memory[symbol] = {
            "count": 1,
            "last_seen": current_time
        }

    else:
        if signal_memory[symbol]["count"] < 3:
         signal_memory[symbol]["count"] += 1
        signal_memory[symbol]["last_seen"] = current_time

    return signal_memory[symbol]["count"]