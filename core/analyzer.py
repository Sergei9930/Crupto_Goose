from core.market_state import get_market_state


def analyze():
    state = get_market_state()

    if not state:
        print("[ANALYZER] Нет данных пока")
        return

    for symbol, exchanges in state.items():
        print(f"\nSYMBOL: {symbol.upper()}")

        binance = exchanges.get("binance")
        bybit = exchanges.get("bybit")

        if not binance or not bybit:
            print("⏳ Ждем обе биржи...")
            continue

        b_buy = binance["buy"]
        b_sell = binance["sell"]

        y_buy = bybit["buy"]
        y_sell = bybit["sell"]

        print(f"Binance → BUY: {b_buy:.2f} | SELL: {b_sell:.2f}")
        print(f"Bybit   → BUY: {y_buy:.2f} | SELL: {y_sell:.2f}")

        # простая логика
        if b_buy > b_sell and y_buy > y_sell:
            print("📈 Давление вверх")
        elif b_sell > b_buy and y_sell > y_buy:
            print("📉 Давление вниз")
        else:
            print("⚖️ Расхождение")