class FilingFetchError(Exception):
    """EDGAR API failed to return filings"""
    pass

class RegimeCheckError(Exception):
    """SPY data unavailable for regime check"""
    pass

class TradeExecutionError(Exception):
    """Alpaca API failed to execute trade"""
    pass

class PositionManagerError(Exception):
    """Position close failed"""
    pass

class PositionCheckError(Exception):
    """Failed to retrieve current Alpaca positions"""
    pass

