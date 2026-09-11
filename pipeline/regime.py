import yfinance as yf
from pipeline.exceptions import RegimeCheckError

def get_current_regime():


    try:
        spy = yf.download("SPY", period = '90d')['Close'].squeeze()
        spy_60d_return = spy.pct_change(60).iloc[-1]

        if spy_60d_return < -0.05:
            return 'bear'
        elif spy_60d_return < -0.02:
            return 'neutral_bear'
        elif spy_60d_return < 0.02:
            return 'neutral'
        elif spy_60d_return < 0.05:
            return 'neutral_bull'
        else:
            return 'bull'
    except RegimeCheckError:
        raise
    except Exception as e:
        raise RegimeCheckError(f"SPY data unavailable for regime check: {e}") from e