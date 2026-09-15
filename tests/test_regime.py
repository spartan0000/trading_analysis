import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
sys.path.append('../pipeline')
from pipeline.regime import get_current_regime

@patch('pipeline.regime.yf.download')
def test_bull_regime(mock_download):
    """SPY up 10% over 60 days should return bull"""
    # Create mock SPY data that's clearly bullish
    prices = pd.Series([100] * 60 + [110] * 10)  # up 10%
    mock_download.return_value = pd.DataFrame({'Close': prices})
    
    result = get_current_regime()
    assert result == 'bull'

@patch('pipeline.regime.yf.download')
def test_bear_regime(mock_download):
    """SPY down 10% over 60 days should return bear"""
    prices = pd.Series([110] * 60 + [100] * 10)  # down ~9%
    mock_download.return_value = pd.DataFrame({'Close': prices})
    
    result = get_current_regime()
    assert result == 'bear'

@patch('pipeline.regime.yf.download')
def test_neutral_regime(mock_download):
    """SPY flat should return neutral"""
    prices = pd.Series([100] * 70)  # flat
    mock_download.return_value = pd.DataFrame({'Close': prices})
    
    result = get_current_regime()
    assert result in ['neutral', 'neutral_bull', 'neutral_bear']

@patch('pipeline.regime.yf.download')
def test_empty_spy_data_raises(mock_download):
    """Empty SPY data should raise RegimeCheckError"""
    from pipeline.exceptions import RegimeCheckError
    mock_download.return_value = pd.DataFrame()
    
    with pytest.raises(RegimeCheckError):
        get_current_regime()