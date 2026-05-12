import asyncio

from ws.binance_ws import run_binance_ws
from ws.bybit_ws import run_bybit_ws

from core.analyzer import analyze


async def analyzer_loop():
    while True:
        await asyncio.sleep(2)
        print("\n[ANALYZER] Анализируем рынок...")
        analyze()


async def main():
    symbol = "solusdt"

    await asyncio.gather(
        run_binance_ws(symbol),
        run_bybit_ws(symbol),
        analyzer_loop()
    )


if __name__ == "__main__":
    asyncio.run(main())