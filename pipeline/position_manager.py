from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, ClosePositionRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import json
import os
from datetime import datetime

from pipeline.regime import get_current_regime
from pathlib import Path


PATH = Path(__file__).parent.parent

client = TradingClient(
    api_key = os.getenv("ALPACA_API_KEY"),
    secret_key = os.getenv("ALPACA_SECRET_KEY"),
    paper = True
)

def execute_trade(signal):
    account = client.get_account()
    portfolio_value = float(account.portfolio_value)
    position_size = portfolio_value * 0.02

    order = MarketOrderRequest(
        symbol=signal['ticker'],
        notional=round(position_size, 2),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    
    result = client.submit_order(order)
    
    # Log the signal details for later analysis
    log_entry = {
        'ticker': signal['ticker'],
        'entry_date': datetime.now().isoformat(),
        'order_id': str(result.id),
        'position_size': position_size,
        'insider_name': signal['insider_name'],
        'purchase_value': signal['purchase_value'],
        'pct_added': signal['pct_added'],
        'regime': get_current_regime()
    }
    
    # Append to log file
    with open(PATH / 'logs' / 'trade_log.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"Executed: {signal['ticker']} ${position_size:.0f}")

def check_close_positions(hold_days=90):
    positions = client.get_all_positions()
    
    # Load trade log to get entry dates
    trade_log = {}
    try:
        with open(PATH / 'logs' / 'trade_log.json', 'r') as f:
            for line in f:
                entry = json.loads(line)
                trade_log[entry['ticker']] = entry
    except FileNotFoundError:
        return
    
    for position in positions:
        ticker = position.symbol
        if ticker not in trade_log:
            continue
            
        entry_date = datetime.fromisoformat(trade_log[ticker]['entry_date'])
        days_held = (datetime.now() - entry_date).days
        current_pl = float(position.unrealized_plpc)
        
        should_close = (
            days_held >= hold_days or          # time stop
            current_pl >= 0.15 or              # take profit at 15%
            current_pl <= -0.10                # stop loss at 10%
        )
        
        if should_close:
            client.close_position(ticker)
            print(f"Closed {ticker}: {days_held} days, {current_pl:.1%} P&L")