import asyncio
import json
import os
import time

import websockets

from signals.signal_queue import get_signals

WS_DIR = "data"
WS_FILE = os.path.join(WS_DIR, "ws_followup_log.jsonl")


async def _binance_snapshot(symbol: str, retries: int = 3):
    url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth20"
    for attempt in range(1, retries + 1):
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as ws:
                raw = await asyncio.wait_for(ws.recv(), timeout=8)
                data = json.loads(raw)
                bids = data.get("bids", [])
                asks = data.get("asks", [])

                buy_volume = sum(float(x[1]) for x in bids[:20])
                sell_volume = sum(float(x[1]) for x in asks[:20])
                best_bid = float(bids[0][0]) if bids else 0
                best_ask = float(asks[0][0]) if asks else 0
                mid = (best_bid + best_ask) / 2 if best_bid > 0 and best_ask > 0 else 0
                return {"exchange": "binance", "mid_price": mid, "buy20": buy_volume, "sell20": sell_volume}
        except Exception as exc:
            await asyncio.sleep(min(2 ** (attempt - 1), 5))
            if attempt == retries:
                print(f"[BINANCE WS SNAPSHOT] failed for {symbol}: {exc}")
    return None


async def _bybit_snapshot(symbol: str, retries: int = 3):
    ws_symbol = symbol.upper()
    url = "wss://stream.bybit.com/v5/public/spot"
    for attempt in range(1, retries + 1):
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as ws:
                sub = {"op": "subscribe", "args": [f"orderbook.50.{ws_symbol}"]}
                await ws.send(json.dumps(sub))

                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=8)
                    payload = json.loads(raw)
                    data = payload.get("data")
                    if not data:
                        continue

                    bids = data.get("b", [])
                    asks = data.get("a", [])
                    if not bids or not asks:
                        continue

                    buy_volume = sum(float(x[1]) for x in bids[:20])
                    sell_volume = sum(float(x[1]) for x in asks[:20])
                    best_bid = float(bids[0][0])
                    best_ask = float(asks[0][0])
                    mid = (best_bid + best_ask) / 2 if best_bid > 0 and best_ask > 0 else 0
                    return {"exchange": "bybit", "mid_price": mid, "buy20": buy_volume, "sell20": sell_volume}
        except Exception as exc:
            await asyncio.sleep(min(2 ** (attempt - 1), 5))
            if attempt == retries:
                print(f"[BYBIT WS SNAPSHOT] failed for {symbol}: {exc}")
    return None


def _append_jsonl(record):
    os.makedirs(WS_DIR, exist_ok=True)
    with open(WS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def _analyze_symbol(symbol, rest_data):
    b_task = _binance_snapshot(symbol)
    y_task = _bybit_snapshot(symbol)
    b_res, y_res = await asyncio.gather(b_task, y_task)

    if not b_res or not y_res:
        return

    b_ratio = b_res["buy20"] / (b_res["sell20"] + 1e-9)
    y_ratio = y_res["buy20"] / (y_res["sell20"] + 1e-9)

    dominance = (rest_data.get("binance_volume_24h", 0) + 1e-9) / (rest_data.get("bybit_volume_24h", 0) + 1e-9)

    lag_hypothesis = "bybit_catch_up" if dominance > 1 and b_ratio > 1 and y_ratio > 1 else "unclear"

    record = {
        "timestamp": time.time(),
        "symbol": symbol,
        "rest_spread": rest_data.get("spread"),
        "rest_binance_price": rest_data.get("binance_price"),
        "rest_bybit_price": rest_data.get("bybit_price"),
        "rest_binance_volume_24h": rest_data.get("binance_volume_24h"),
        "rest_bybit_volume_24h": rest_data.get("bybit_volume_24h"),
        "binance_mid": b_res["mid_price"],
        "bybit_mid": y_res["mid_price"],
        "binance_ob_ratio_buy_to_sell": b_ratio,
        "bybit_ob_ratio_buy_to_sell": y_ratio,
        "volume_dominance_ratio_binance_to_bybit": dominance,
        "lag_hypothesis": lag_hypothesis,
    }
    _append_jsonl(record)
    print(f"[WS FOLLOWUP] {symbol}: lag_hypothesis={lag_hypothesis}")


def run_ws_followup_for_active_signals(sample_seconds=8):
    signals = get_signals()
    if not signals:
        return

    # Analyze only active/new signals
    active = {s: d for s, d in signals.items() if d.get("status") in {"new", "done", "processing"}}
    if not active:
        return

    async def _runner():
        tasks = [_analyze_symbol(symbol, data) for symbol, data in active.items()]
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=max(sample_seconds, 8))

    try:
        asyncio.run(_runner())
    except Exception as exc:
        print(f"[WS FOLLOWUP] failed: {exc}")
