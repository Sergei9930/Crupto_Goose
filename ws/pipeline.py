import asyncio
import json
import os
import time

import websockets

from signals.signal_queue import get_signals

WS_DIR = "data"
WS_FILE = os.path.join(WS_DIR, "ws_followup_log.jsonl")


def _safe_ratio(a, b):
    return a / (b + 1e-9)


def _build_verdict(rest_data, b_res, y_res):
    b_ratio = _safe_ratio(b_res["buy20"], b_res["sell20"])
    y_ratio = _safe_ratio(y_res["buy20"], y_res["sell20"])

    dominance = _safe_ratio(
        rest_data.get("binance_volume_24h", 0),
        rest_data.get("bybit_volume_24h", 0),
    )

    live_premium_pct = 0.0
    if y_res["mid_price"] > 0:
        live_premium_pct = ((b_res["mid_price"] - y_res["mid_price"]) / y_res["mid_price"]) * 100

    # Leader exchange by daily volume
    leader = "binance" if dominance >= 1 else "bybit"

    # Pressure direction on each exchange
    b_pressure = "buy" if b_ratio > 1 else "sell"
    y_pressure = "buy" if y_ratio > 1 else "sell"

    # Catch-up hypothesis + probable direction
    verdict = "unclear"
    probable_move = "flat"

    if leader == "binance":
        if live_premium_pct > 0 and b_pressure == "buy" and y_pressure == "buy":
            verdict = "bybit_may_catch_up_to_binance"
            probable_move = "up"
        elif live_premium_pct > 0 and b_pressure == "sell" and y_pressure == "sell":
            verdict = "bybit_may_catch_down_to_binance"
            probable_move = "down"
    else:
        if live_premium_pct < 0 and b_pressure == "buy" and y_pressure == "buy":
            verdict = "binance_may_catch_up_to_bybit"
            probable_move = "up"
        elif live_premium_pct < 0 and b_pressure == "sell" and y_pressure == "sell":
            verdict = "binance_may_catch_down_to_bybit"
            probable_move = "down"

    return {
        "leader_exchange_by_24h_volume": leader,
        "binance_ob_ratio_buy_to_sell": b_ratio,
        "bybit_ob_ratio_buy_to_sell": y_ratio,
        "volume_dominance_ratio_binance_to_bybit": dominance,
        "live_price_premium_pct_binance_vs_bybit": live_premium_pct,
        "binance_pressure": b_pressure,
        "bybit_pressure": y_pressure,
        "verdict": verdict,
        "probable_move": probable_move,
    }


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
    b_res, y_res = await asyncio.gather(_binance_snapshot(symbol), _bybit_snapshot(symbol))
    if not b_res or not y_res:
        return

    verdict_data = _build_verdict(rest_data, b_res, y_res)

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
        **verdict_data,
    }

    _append_jsonl(record)
    print(f"[WS FOLLOWUP] {symbol}: {record['verdict']} ({record['probable_move']})")


def run_ws_followup_for_active_signals(sample_seconds=8):
    signals = get_signals()
    if not signals:
        return

    # analyze only fresh signals to avoid duplicate heavy ws usage
    active = {s: d for s, d in signals.items() if d.get("status") == "new"}
    if not active:
        return

    async def _runner():
        tasks = [_analyze_symbol(symbol, data) for symbol, data in active.items()]
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=max(sample_seconds, 8))

    try:
        asyncio.run(_runner())
    except Exception as exc:
        print(f"[WS FOLLOWUP] failed: {exc}")
