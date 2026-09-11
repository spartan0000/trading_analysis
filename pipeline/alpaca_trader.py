import os
from dotenv import load_dotenv
import json
import logging
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from pathlib import Path
from pipeline.exceptions import TradeExecutionError

load_dotenv()

PATH = Path(__file__).parent.parent
LOG_DIR = Path(os.environ.get("LOG_DIR", PATH / "logs"))

def get_client():
    return TradingClient(
        api_key=os.getenv("ALPACA_API_KEY"),
        secret_key=os.getenv("ALPACA_SECRET_KEY"),
        paper=True
    )

def execute_trade(signal, regime):
    client = get_client()
    account = client.get_account()
    portfolio_value = float(account.portfolio_value)
    position_size = portfolio_value * 0.02 #2% of portfolio

    try:
        order = MarketOrderRequest(
            symbol = signal['ticker'],
            notional = round(position_size, 2),
            side = OrderSide.BUY,
            time_in_force = TimeInForce.DAY
        )
        result = client.submit_order(order)

        log_signal({
            'date': datetime.now().isoformat(),
            'ticker': signal['ticker'],
            'insider_name': signal['insider_name'],
            'officer_title': signal.get('officer_title'),
            'purchase_value': signal['purchase_value'],
            'pct_added': signal['pct_added'],
            'DirectIndirect': signal['DirectIndirect'],
            'filing_lag': signal['filing_lag'],
            'regime': regime,
            'position_size': position_size,
            'alpaca_order_id': str(result.id),
            'action': 'BUY'
        })
        
        logging.info(f"BUY {signal['ticker']} ${position_size:.0f} — {signal['insider_name']}")
        return result
        
    except Exception as e:
        logging.error(f"Order failed {signal['ticker']}: {e}")
        raise TradeExecutionError(f"Failed to execute trade for {signal['ticker']}: {e}") from e
        return None

def log_signal(entry):
    """Append signal to JSONL log"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / 'signals_log.jsonl', 'a') as f:
        f.write(json.dumps(entry) + '\n')
