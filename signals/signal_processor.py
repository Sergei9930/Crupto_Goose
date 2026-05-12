import time

from signals.signal_queue import get_signals, cleanup_signals, COOLDOWN_TIME


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

        # ⛔ cooldown — не обрабатываем слишком часто
        if current_time - last_processed < COOLDOWN_TIME:
            continue

        print("-----")
        print(f"Symbol: {symbol}")
        print(f"Spread: {round(spread, 2)} %")

        # меняем статус
        data["status"] = "processing"

        # 🔍 базовая логика (пока заглушка)
        if spread > 1:
            print("🔥 Сильный сигнал (интересный)")
        else:
            print("⚪ Слабый сигнал")

        # обновляем время обработки
        data["last_processed"] = current_time

        # помечаем как обработанный
        data["status"] = "done"