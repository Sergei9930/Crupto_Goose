import json
import os
import time

from signals.signal_queue import get_signals, cleanup_signals, COOLDOWN_TIME

SIGNALS_DIR = "data"
SIGNALS_FILE = os.path.join(SIGNALS_DIR, "signals_log.jsonl")


def _append_jsonl(record):
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    with open(SIGNALS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def process_signals():
    cleanup_signals()
    signals = get_signals()

    if not signals:
        print("[PROCESSOR] Нет сигналов")
        return

    print("[PROCESSOR] Обрабатываем сигналы...")
    current_time = time.time()

    for symbol, data in signals.items():
        spread = data["spread"]
        last_processed = data["last_processed"]

        if current_time - last_processed < COOLDOWN_TIME:
            continue

        print("-----")
        print(f"Symbol: {symbol}")
        print(f"Spread: {round(spread, 2)} %")

        data["status"] = "processing"

        if spread > 1:
            print("🔥 Сильный сигнал (интересный)")
        else:
            print("⚪ Слабый сигнал")

        dominance_ratio = (data.get("binance_volume_24h", 0) + 1e-9) / (data.get("bybit_volume_24h", 0) + 1e-9)

        record = {
            "timestamp": current_time,
            "symbol": symbol,
            "spread": spread,
            "binance_price": data.get("binance_price"),
            "bybit_price": data.get("bybit_price"),
            "binance_volume_24h": data.get("binance_volume_24h"),
            "bybit_volume_24h": data.get("bybit_volume_24h"),
            "volume_dominance_ratio_binance_to_bybit": dominance_ratio,
            "status": "processed",
        }
        _append_jsonl(record)

        data["last_processed"] = current_time
        data["status"] = "done"
