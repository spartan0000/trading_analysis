import pytest
import pandas as pd

@pytest.fixture
def sample_filings():
    """Representative sample of Form 4 filings"""
    return pd.DataFrame([
        {
            'ticker': 'TSLA',
            'company': 'Tesla Inc',
            'insider_name': 'Elon Musk',
            'officer_title': 'CEO',
            'purchase_value': 750000,
            'pct_added': 0.0023,
            'DirectIndirect': 'I',
            'filing_lag': 1,
            'TransactionType': 'Purchase',
            'form': 4,
            'EquitySwap': False,
            'is_officer': 1,
            'is_ceo': 1,
            'is_director': 1,
            'is_ten_pct_owner': 1,
            'alpha': 0.089,
            'beat_market': 1
        },
        {
            # Token purchase — should be filtered out
            'ticker': 'TPL',
            'company': 'Texas Pacific Land',
            'insider_name': 'Murray Stahl',
            'officer_title': None,
            'purchase_value': 1294,
            'pct_added': 0.0002,
            'DirectIndirect': 'I',
            'filing_lag': 1,
            'TransactionType': 'Purchase',
            'form': 4,
            'EquitySwap': False,
            'is_officer': 0,
            'is_ceo': 0,
            'is_director': 1,
            'is_ten_pct_owner': 0,
            'alpha': -0.35,
            'beat_market': 0
        },
        {
            # High value signal
            'ticker': 'TKO',
            'company': 'TKO Group Holdings',
            'insider_name': 'Ariel Emanuel',
            'officer_title': 'Chief Executive Officer',
            'purchase_value': 850000,
            'pct_added': 0.0052,
            'DirectIndirect': 'I',
            'filing_lag': 1,
            'TransactionType': 'Purchase',
            'form': 4,
            'EquitySwap': False,
            'is_officer': 1,
            'is_ceo': 1,
            'is_director': 1,
            'is_ten_pct_owner': 1,
            'alpha': 0.122,
            'beat_market': 1
        },
        {
            # Late filing — should be filtered
            'ticker': 'AAPL',
            'company': 'Apple Inc',
            'insider_name': 'Tim Cook',
            'officer_title': 'CEO',
            'purchase_value': 600000,
            'pct_added': 0.01,
            'DirectIndirect': 'D',
            'filing_lag': 10,  # too late
            'TransactionType': 'Purchase',
            'form': 4,
            'EquitySwap': False,
            'is_officer': 1,
            'is_ceo': 1,
            'is_director': 0,
            'is_ten_pct_owner': 0,
            'alpha': 0.05,
            'beat_market': 1
        }
    ])