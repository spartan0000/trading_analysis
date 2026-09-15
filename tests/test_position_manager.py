import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import sys
sys.path.append('../pipeline')
from pipeline.position_manager import check_close_positions

def make_mock_position(symbol, pl_pct):
    position = MagicMock()
    position.symbol = symbol
    position.unrealized_plpc = str(pl_pct)
    return position

@patch('pipeline.position_manager.get_client')
@patch('pipeline.position_manager.get_entry_dates')
def test_close_on_take_profit(mock_entry_dates, mock_get_client):
    """Position at 15% gain should close"""
    client = MagicMock()
    mock_get_client.return_value = client
    
    # Position held 10 days, up 15%
    entry = datetime.now(timezone.utc) - timedelta(days=10)
    mock_entry_dates.return_value = {'TSLA': entry}
    client.get_all_positions.return_value = [
        make_mock_position('TSLA', 0.15)
    ]
    
    closed = check_close_positions()
    
    assert 'TSLA' in closed
    client.close_position.assert_called_once_with('TSLA')

@patch('pipeline.position_manager.get_client')
@patch('pipeline.position_manager.get_entry_dates')
def test_close_on_stop_loss(mock_entry_dates, mock_get_client):
    """Position down 10% should close"""
    client = MagicMock()
    mock_get_client.return_value = client
    
    entry = datetime.now(timezone.utc) - timedelta(days=5)
    mock_entry_dates.return_value = {'TSLA': entry}
    client.get_all_positions.return_value = [
        make_mock_position('TSLA', -0.10)
    ]
    
    closed = check_close_positions()
    
    assert 'TSLA' in closed
    client.close_position.assert_called_once_with('TSLA')

@patch('pipeline.position_manager.get_client')
@patch('pipeline.position_manager.get_entry_dates')
def test_close_on_time_stop(mock_entry_dates, mock_get_client):
    """Position held 90 days should close"""
    client = MagicMock()
    mock_get_client.return_value = client
    
    entry = datetime.now(timezone.utc) - timedelta(days=90)
    mock_entry_dates.return_value = {'TSLA': entry}
    client.get_all_positions.return_value = [
        make_mock_position('TSLA', 0.03)  # small gain, not at profit target
    ]
    
    closed = check_close_positions()
    
    assert 'TSLA' in closed

@patch('pipeline.position_manager.get_client')
@patch('pipeline.position_manager.get_entry_dates')
def test_no_close_when_holding(mock_entry_dates, mock_get_client):
    """Position held 30 days with 5% gain should not close"""
    client = MagicMock()
    mock_get_client.return_value = client
    
    entry = datetime.now(timezone.utc) - timedelta(days=30)
    mock_entry_dates.return_value = {'TSLA': entry}
    client.get_all_positions.return_value = [
        make_mock_position('TSLA', 0.05)
    ]
    
    closed = check_close_positions()
    
    assert 'TSLA' not in closed
    client.close_position.assert_not_called()

@patch('pipeline.position_manager.get_client')
@patch('pipeline.position_manager.get_entry_dates')
def test_no_entry_date_skips(mock_entry_dates, mock_get_client):
    """Position with no buy order found should be skipped"""
    client = MagicMock()
    mock_get_client.return_value = client
    
    mock_entry_dates.return_value = {}  # no entry dates found
    client.get_all_positions.return_value = [
        make_mock_position('TSLA', 0.20)  # even if profitable
    ]
    
    closed = check_close_positions()
    
    assert 'TSLA' not in closed
    client.close_position.assert_not_called()