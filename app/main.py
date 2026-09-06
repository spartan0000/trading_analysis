from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Relative to app/main.py → go up one level to project root → data/
DATA_PATH = Path(__file__).parent.parent / "data" / "returns_analysis_filtered.csv"

@app.get("/data")
async def get_data():
    df = pd.read_csv(DATA_PATH)
    df = df.replace({np.nan: None})
    return df.to_dict(orient="records")

@app.get("/data/filtered")
async def get_filtered(
    min_value: float = 500000,
    max_value: float = 1000000,
    max_lag: int = 5
):
    df = pd.read_csv(DATA_PATH)
    df_filtered = df[
        (df['purchase_value'] >= min_value) &
        (df['purchase_value'] < max_value) &
        (df['filing_lag'] <= max_lag) &
        (df['TransactionType'] == 'Purchase')
    ]
    df_filtered = df_filtered.replace({np.nan: None})
    return df_filtered.to_dict(orient="records")

@app.get("/data/info")
async def get_info():
    df = pd.read_csv(DATA_PATH)
    return {
        "total_rows": len(df),
        "date_range": [str(df['Date'].min()), str(df['Date'].max())],
        "tickers": int(df['ticker'].nunique()),
        "beat_rate": float(df['beat_market'].mean()),
        "avg_alpha": float(df['alpha'].mean()),
        "columns": df.columns.tolist()
    }