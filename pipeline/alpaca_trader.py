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
import boto3

load_dotenv()

PATH = Path(__file__).parent.parent
LOG_DIR = Path(os.environ.get("LOG_DIR", PATH / "logs"))


print(f"ALPACA KEY present: {bool(os.getenv('ALPACA_API_KEY'))}")
print(f"ALPACA SECRET present: {bool(os.getenv('ALPACA_SECRET_KEY'))}")

def get_client():
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")

    if not key or not secret:
        raise ValueError(f"Alpaca credentials missing - KEY: {bool(key)}; SECRET: {bool(secret)}")
    
    return TradingClient(
        api_key=key,
        secret_key=secret,
        paper=True
    )
def send_trade_alert(signal, position_size, order):
    """Send email notification for executed trade"""
    topic_arn = os.getenv("SNS_TOPIC_ARN")
    if not topic_arn:
        logging.warning("SNS_TOPIC_ARN not set — skipping alert")
        return
    
    try:
        sns = boto3.client('sns', region_name='us-east-1')
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Trade Executed: {signal['ticker']}",
            Message=f"""
Insider Trading Signal Executed
================================
Ticker:         {signal['ticker']}
Company:        {signal['company']}
Insider:        {signal['insider_name']}
Title:          {signal.get('officer_title', 'N/A')}
Purchase Value: ${signal['purchase_value']:,.0f}
Pct Added:      {signal['pct_added']:.2%}
Ownership:      {signal['DirectIndirect']}
Filing Lag:     {signal['filing_lag']} days
Regime:         {signal['regime']}

Position Size:  ${position_size:,.0f}
Order ID:       {order.id}

Check Alpaca paper account for execution details.
            """.strip()
        )
        logging.info(f"Trade alert sent for {signal['ticker']}")
    except Exception as e:
        logging.error(f"SNS alert failed: {e}")
        # Don't raise — alert failure shouldn't fail the pipeline

def execute_trade(signal, regime):
    client = get_client()
    
    account = client.get_account()
    portfolio_value = float(account.portfolio_value)
    position_size = round(portfolio_value * 0.02, 2)
    
    try:
        order = MarketOrderRequest(
            symbol=signal['ticker'],
            notional=position_size,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        result = client.submit_order(order)
        
        # Log the signal
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
            'alpaca_order_id': str(result.id)
        })
        
        # Send email alert
        send_trade_alert(signal, position_size, result)
        
    except Exception as e:
        logging.error(f"Order failed {signal['ticker']}: {e}")
        raise TradeExecutionError(f"Failed to execute trade for {signal['ticker']}: {e}") from e

def log_signal(entry):
    """Append signal to JSONL log"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / 'signals_log.jsonl', 'a') as f:
        f.write(json.dumps(entry) + '\n')
