import asyncio
import json
import websockets

from core.market_state import update_market_state


async def run_binance_ws(symbol="solusdt"):
    url = f"wss://stream.binance.com:9443/ws/{symbol}@depth20"

    print(f"[BINANCE WS] {symbol.upper()}")

    async with websockets.connect(url) as ws:
        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            bids = data.get("bids", [])
            asks = data.get("asks", [])

            buy_volume = sum(float(b[1]) for b in bids)
            sell_volume = sum(float(a[1]) for a in asks)

            update_market_state(symbol, "binance", {
                "buy": buy_volume,
                "sell": sell_volume
            })