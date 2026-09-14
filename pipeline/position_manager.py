import os
from datetime import datetime, timedelta, timezone

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus
from pipeline.exceptions import PositionManagerError
import boto3
import logging

client = TradingClient(
    api_key = os.getenv("ALPACA_API_KEY"),
    secret_key = os.getenv("ALPACA_SECRET_KEY"),
    paper = True
)

def get_entry_dates(lookback_days):
    """Map each symbol to the fill time of its most recent buy, from Alpaca's
    order history. The strategy never adds to an open position, so the latest
    filled buy is that position's entry."""
    orders = client.get_orders(filter=GetOrdersRequest(
        status=QueryOrderStatus.CLOSED,
        side=OrderSide.BUY,
        after=datetime.now(timezone.utc) - timedelta(days=lookback_days),
        limit=500,
    ))
    entry_dates = {}
    for o in sorted(orders, key=lambda o: o.submitted_at):
        if o.filled_at is not None:
            entry_dates[o.symbol] = o.filled_at  # sorted ascending → last write is most recent
    return entry_dates

def send_close_alert(symbol, days_held, pl_pct, reason):
    topic_arn = os.getenv("SNS_TOPIC_ARN")
    if not topic_arn:
        return
    
    try:
        sns = boto3.client('sns', region_name='us-east-1')
        emoji = "✓" if pl_pct > 0 else "✗"
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Position Closed: {symbol} {emoji} {pl_pct:.1%}",
            Message=f"""
Position Closed
===============
Ticker:      {symbol}
Days Held:   {days_held}
P&L:         {pl_pct:.2%}
Reason:      {reason}

Check Alpaca for full details.
            """.strip()
        )
    except Exception as e:
        logging.error(f"Close alert failed: {e}")

def check_close_positions(hold_days=90):
    try:
        positions = client.get_all_positions()
        entry_dates = get_entry_dates(lookback_days=hold_days * 2)

        closed = []
        for position in positions:
            ticker = position.symbol
            entry_date = entry_dates.get(ticker)
            if entry_date is None:
                print(f"No buy order found for {ticker} in history — skipping")
                continue

            days_held = (datetime.now(timezone.utc) - entry_date).days
            current_pl = float(position.unrealized_plpc)

            reason = None
            if current_pl <= -0.10:
                reason = f"stop_loss ({current_pl:.1%})"
            elif current_pl >= 0.15:
                reason = f"take_profit ({current_pl:.1%})"
            elif days_held >= hold_days:
                reason = f"time_stop ({days_held} days)"

            if reason:
                client.close_position(ticker)
                logging.info(f"Closed {ticker}: {reason}")
                print(f"Closed {ticker}: {days_held} days, {current_pl:.1%} P&L")
                send_close_alert(ticker, days_held, current_pl, reason)
                closed.append(ticker)

        return closed
    except Exception as e:
        raise PositionManagerError(f"Failed to check/close positions: {e}") from e
