import os
from datetime import datetime, timedelta, timezone

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus

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

def check_close_positions(hold_days=90):
    positions = client.get_all_positions()
    entry_dates = get_entry_dates(lookback_days=hold_days * 2)

    for position in positions:
        ticker = position.symbol
        entry_date = entry_dates.get(ticker)
        if entry_date is None:
            print(f"No buy order found for {ticker} in history — skipping")
            continue

        days_held = (datetime.now(timezone.utc) - entry_date).days
        current_pl = float(position.unrealized_plpc)

        should_close = (
            days_held >= hold_days or          # time stop
            current_pl >= 0.15 or              # take profit at 15%
            current_pl <= -0.10                # stop loss at 10%
        )

        if should_close:
            client.close_position(ticker)
            print(f"Closed {ticker}: {days_held} days, {current_pl:.1%} P&L")
