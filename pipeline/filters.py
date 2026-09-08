import os
from alpaca.trading.client import TradingClient

MIN_VALUE = 10000
MAX_VALUE = 100000000
MAX_LAG = 5
MIN_SHARES = 10

def apply_filters(df, min_value=MIN_VALUE, max_value=MAX_VALUE, max_lag=MAX_LAG, min_shares=MIN_SHARES):
    return df[
        (df['purchase_value'] >= min_value) &
        (df['purchase_value'] < max_value) &
        (df['filing_lag'] <= max_lag) &
        (df['TransactionType'] == 'Purchase') &
        (df['form'] == 4) &
        (df['EquitySwap'] == False) &
        (df['Shares'] > min_shares)
    ].copy()

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