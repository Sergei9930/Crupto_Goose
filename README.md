# Crupto_Goose

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Notes
- Main loop scans Binance/Bybit REST every 3 seconds.
- Confirmed symbols are passed into websocket follow-up.
- Logs are written to `data/signals_log.jsonl` and `data/ws_followup_log.jsonl`.
