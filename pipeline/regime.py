import yfinance as yf

def get_current_regime():

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