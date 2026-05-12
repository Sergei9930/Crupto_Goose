import asyncio
import json
import websockets

from core.market_state import update_market_state


async def run_bybit_ws(symbol="solusdt"):

    ws_symbol = symbol.upper()
    url = "wss://stream.bybit.com/v5/public/spot"

    print(f"[BYBIT WS] Подключаемся к {ws_symbol}")

    # 👉 ХРАНИМ СТАКАН
    orderbook = {
        "bids": {},
        "asks": {}
    }

    async with websockets.connect(url) as ws:

        subscribe_msg = {
            "op": "subscribe",
            "args": [f"orderbook.50.{ws_symbol}"]
        }

        await ws.send(json.dumps(subscribe_msg))
        print(f"[BYBIT WS] Подписка отправлена: {ws_symbol}")

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)

                if "data" not in data:
                    continue

                ob = data["data"]

                bids = ob.get("b", [])
                asks = ob.get("a", [])

                # 👉 ОБНОВЛЯЕМ BIDS
                for price, volume in bids:
                    price = float(price)
                    volume = float(volume)

                    if volume == 0:
                        orderbook["bids"].pop(price, None)
                    else:
                        orderbook["bids"][price] = volume

                # 👉 ОБНОВЛЯЕМ ASKS
                for price, volume in asks:
                    price = float(price)
                    volume = float(volume)

                    if volume == 0:
                        orderbook["asks"].pop(price, None)
                    else:
                        orderbook["asks"][price] = volume

                # ❗ если стакан ещё пустой — пропускаем
                if len(orderbook["bids"]) < 10 or len(orderbook["asks"]) < 10:
                    continue

                # 👉 сортируем
                top_bids = sorted(orderbook["bids"].items(), reverse=True)[:20]
                top_asks = sorted(orderbook["asks"].items())[:20]

                buy_volume = sum(v for _, v in top_bids)
                sell_volume = sum(v for _, v in top_asks)

                print(f"\n[BYBIT FULL] {ws_symbol}")
                print(f"BUY volume: {round(buy_volume, 2)}")
                print(f"SELL volume: {round(sell_volume, 2)}")

                if buy_volume > sell_volume:
                    print("🟢 Давление вверх")
                else:
                    print("🔴 Давление вниз")

                update_market_state(
                    symbol.lower(),
                    "bybit",
                    {
                        "buy": buy_volume,
                        "sell": sell_volume
                    }
                )

                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"[BYBIT ERROR] {e}")
                await asyncio.sleep(1)