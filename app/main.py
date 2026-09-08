import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import numpy as np
from datetime import datetime

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient

from pipeline.filters import apply_analysis_filters, MAX_ANALYSIS_VALUE, MIN_ANALYSIS_VALUE, MAX_ANALYSIS_LAG, MIN_ANALYSIS_SHARES

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = False,
    allow_methods=["*"],
    allow_headers=["*"],
)
### the data files need to be renamed here - not sure these are the correct ones for the corresponding endpoints
# Relative to app/main.py → go up one level to project root → data/
PATH = Path(__file__).parent.parent
DATA_PATH = PATH / "data"

FULL_DATA_PATH = DATA_PATH / "returns_analysis.csv"
FILTERED_DATA_PATH = DATA_PATH / "returns_analysis_filtered.csv"

@app.get("/data")
async def get_data():
    df = pd.read_csv(FULL_DATA_PATH)
    df = df.replace({np.nan: None})
    return df.to_dict(orient="records")

@app.get("/data/filtered")
async def get_filtered(
    min_value: float = MIN_ANALYSIS_VALUE,
    max_value: float = MAX_ANALYSIS_VALUE,
    max_lag: int = MAX_ANALYSIS_LAG,
    min_shares: int = MIN_ANALYSIS_SHARES,
):
    df = pd.read_csv(FULL_DATA_PATH)

    apply_analysis_filters(df)

    df_filtered = apply_analysis_filters(df, min_value, max_value, max_lag)
    df_filtered = df_filtered.replace({np.nan: None})
    return df_filtered.to_dict(orient="records")

@app.get("/data/info")
async def get_info():
    df = pd.read_csv(FULL_DATA_PATH)
    return {
        "total_rows": len(df),
        "date_range": [str(df['Date'].min()), str(df['Date'].max())],
        "tickers": int(df['ticker'].nunique()),
        "beat_rate": float(df['beat_market'].mean()),
        "avg_alpha": float(df['alpha'].mean()),
        "columns": df.columns.tolist()
    }


#for a vite dashboard that pulls and displays signals

@app.get("/logs/signals")
async def get_signals():
    signals = []
    try:
        with open(PATH / "logs" / "signals_log.jsonl") as f:
            for line in f:
                signals.append(json.loads(line))
    except FileNotFoundError:
        return []
    return signals

@app.get("/logs/positions")
async def get_positions():
    positions = []
    try:
        with open(PATH / "logs" / "positions_log.jsonl") as f:
            for line in f:
                positions.append(json.loads(line))
    except FileNotFoundError:
        return []
    return positions

@app.get("/alpaca/positions")
async def get_alpaca_positions():
    client = TradingClient(
        api_key = os.getenv("ALPACA_API_KEY"),
        secret_key = os.getenv("ALPACA_SECRET_KEY"),
        paper = True
    )

    positions = client.get_all_positions()
    return [p.model_dump() for p in positions]

    