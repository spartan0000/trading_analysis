import os
from alpaca.trading.client import TradingClient

MIN_ANALYSIS_VALUE = 10000
MAX_ANALYSIS_VALUE = 100000000
MAX_ANALYSIS_LAG = 5
MIN_ANALYSIS_SHARES = 10



# Used by analysis / FastAPI — slice historical data for research
def apply_analysis_filters(df, min_value=MIN_ANALYSIS_VALUE, max_value=MAX_ANALYSIS_VALUE, max_lag=MAX_ANALYSIS_LAG):
    return df[
        (df['purchase_value'] >= min_value) &
        (df['purchase_value'] < max_value) &
        (df['filing_lag'] <= max_lag) &
        (df['TransactionType'] == 'Purchase') &
        (df['form'] == 4) &
        (df['EquitySwap'] == False)
    ].copy()

# Used by trading pipeline — evaluate a single new signal
def passes_trade_criteria(signal, regime, existing_positions):
    return all([
        signal['purchase_value'] >= 500000,
        signal['purchase_value'] < 1000000,
        signal['filing_lag'] <= 5,
        signal['TransactionType'] == 'Purchase',
        signal['form'] == 4,
        not signal['EquitySwap'],
        regime in ['bull', 'neutral_bull'],
        signal['ticker'] not in existing_positions,
        len(existing_positions) < 10
    ])

def already_holding():
    client = TradingClient(
        api_key = os.getenv("ALPACA_API_KEY"),
        secret_key = os.getenv("ALPACA_SECRET_KEY"),
        paper = True
    )
    positions = client.get_all_positions()
    return {p.symbol for p in positions}

def passes_criteria(signal, regime, existing_positions):
    checks = [
        # Add regime check — only trade in bull or neutral_bull
        regime in ['bull', 'neutral_bull'],
        # Don't add to existing position
        signal['ticker'] not in existing_positions,

        signal['DirectIndirect'] == 'I',
    ]
    return all(checks)