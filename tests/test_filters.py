import pytest
import sys
sys.path.append('../pipeline')
from pipeline.filters import apply_analysis_filters, passes_trade_criteria

def test_filter_removes_token_purchases(sample_filings):
    """Murray Stahl 1-share purchases should be filtered"""
    filtered = apply_analysis_filters(sample_filings)
    assert 'Murray Stahl' not in filtered['insider_name'].values

def test_filter_removes_late_filings(sample_filings):
    """Filings with lag > 5 days should be filtered"""
    filtered = apply_analysis_filters(sample_filings)
    assert all(filtered['filing_lag'] <= 5)

def test_filter_keeps_valid_signals(sample_filings):
    """TSLA and TKO should pass the filter"""
    filtered = apply_analysis_filters(sample_filings)
    assert 'TSLA' in filtered['ticker'].values
    assert 'TKO' in filtered['ticker'].values

def test_filter_value_range(sample_filings):
    """All filtered purchases should be in 500k-1m range"""
    filtered = apply_analysis_filters(sample_filings)
    assert all(filtered['purchase_value'] >= 500000)
    assert all(filtered['purchase_value'] < 1000000)

def test_passes_trade_criteria_bull_regime(sample_filings):
    """Valid signal in bull regime should pass"""
    signal = sample_filings[sample_filings['ticker'] == 'TSLA'].iloc[0]
    assert passes_trade_criteria(signal, 'bull', set()) == True

def test_passes_trade_criteria_neutral_regime(sample_filings):
    """Valid signal in neutral regime should fail"""
    signal = sample_filings[sample_filings['ticker'] == 'TSLA'].iloc[0]
    assert passes_trade_criteria(signal, 'neutral', set()) == False

def test_passes_trade_criteria_existing_position(sample_filings):
    """Should not trade if already holding the ticker"""
    signal = sample_filings[sample_filings['ticker'] == 'TSLA'].iloc[0]
    assert passes_trade_criteria(signal, 'bull', {'TSLA'}) == False

def test_passes_trade_criteria_max_positions(sample_filings):
    """Should not trade if at max concurrent positions"""
    signal = sample_filings[sample_filings['ticker'] == 'TSLA'].iloc[0]
    existing = {'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSMC', 'V', 'MA', 'JPM'}
    assert passes_trade_criteria(signal, 'bull', existing) == False