# Architecture

Two parts:

1. **Research pipeline** — `edgarForm4.py` → `edgarAnalysis.py` → `app/main.py` (FastAPI).
   Backtests whether insider Form 4 purchases beat SPY. Read-only, no scheduler.

2. **Live trading pipeline** (`pipeline/`) — runs daily as an AWS Lambda container
   (`lambda_function.py` + `dockerfile`). `run_daily.py` orchestrates: close due
   positions → check market regime → fetch yesterday's Form 4 filings → filter
   signals (`filters.passes_trade_criteria`) → execute paper trades via Alpaca.
   Position entry dates come from Alpaca's own order history, so no external
   state store is required.

## Planned

- Add `boto3` + Amazon SNS to `pipeline/alpaca_trader.py` so a successful trade
  publishes to an SNS topic (email subscription) — not yet implemented.
