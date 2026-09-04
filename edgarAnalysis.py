import yfinance as yf
from datetime import timedelta
import pandas as pd
import os
from collections import Counter


#get and cache spy prices
spy_cache = "spy_cache.parquet"

if os.path.exists(spy_cache):
    spy_prices = pd.read_parquet(spy_cache)
else:


    spy_prices = yf.download('SPY', start = "2020-01-01", end = "2026-06-30", progress=False)
    spy_prices.columns = spy_prices.columns.droplevel(1)
    spy_prices.to_parquet(spy_cache)



#cached prices for the entire sp500
all_prices = pd.read_parquet('sp500_prices.parquet')








def get_spy_return(purchase_date: str, days = 90, min_trading_days=60):
    start = pd.to_datetime(purchase_date)
    end = start + timedelta(days=days)

    mask = (spy_prices.index >= start) & (spy_prices.index <= end)

    window = spy_prices[mask]

    window.dropna(inplace=True)

    if len(window) < 2:
        return None, 'not_enough_spy_data'
    if len(window) < min_trading_days:
        return None, 'not_enough_spy_trading_days'
    return float((window['Close'].iloc[-1] - window['Close'].iloc[0])/window['Close'].iloc[0]), 'ok'






def calculate_returns(ticker: str, purchase_date: str, days=90, min_trading_days=60):
    start = pd.to_datetime(purchase_date)
    end = start + timedelta(days=days)
    


    try:
        prices = all_prices['Close'][ticker].dropna()
    except KeyError:
        return None, 'ticker_not_in_parquet'
    
    window = prices[(prices.index >= start) & (prices.index < end)]

             

    if len(window) < 2:
        return None, 'not_enough_stock_data'
    if len(window) < min_trading_days:
        return None, 'not_enough_stock_trading_days'

        

    stock_return = (window.iloc[-1] - window.iloc[0])/window.iloc[0]
    spy_return, status = get_spy_return(purchase_date)

    if spy_return is None:
        return None, status

    alpha = stock_return - spy_return

    return {
        'stock_return': float(stock_return),
        'spy_return': float(spy_return),
        'alpha': float(alpha),
        'beat_market': int(alpha > 0)
    }, 'ok'




if os.path.exists("returns_analysis.csv"):
    os.remove("returns_analysis.csv")

error_counts = Counter()

n = 0
results = 0

df = pd.read_csv('insider_purchases_2025.csv')
df['Date'] = df['Date'].str.extract(r'(\d{4}-\d{2}-\d{2})')[0] #weird footnote in the date messing things up - extract just date using regex

for _, row in df.iterrows():
    
    n += 1
    result, status = calculate_returns(row['ticker'], row['Date'])
    if result:
        result['ticker'] = row['ticker']
        result['Date'] = row['Date']
        result['insider_name'] = row['insider_name']
        result['officer_title'] = row['officer_title']
        result['Security'] = row['Security']
        result['filing_date'] = row['filing_date']
        result['Shares'] = row['Shares']
        result['Remaining'] = row['Remaining']
        result['Price'] = row['Price']
        result['AcquiredDisposed'] = row['AcquiredDisposed']
        result['DirectIndirect'] = row['DirectIndirect']
        result['NatureOfOwnership'] = row['NatureOfOwnership']
        result['form'] = row['form']
        result['EquitySwap'] = row['EquitySwap']
        result['TransactionType'] = row['TransactionType']
        result['is_officer'] = int(row['is_officer'])
        result['is_director'] = int(row['is_director'])
        title = str(row['officer_title']).lower() if pd.notna(row['officer_title']) else ''
        result['is_ceo'] = int('ceo' in title or 'chief executive' in title)
        result['is_non_ceo_officer'] = int(result['is_officer'] == 1 and result['is_ceo'] == 0)
        result['is_ten_pct_owner'] = int(row['is_ten_pct_owner'])
        result['company'] = row['company']
        stake_before = row['Remaining'] - row['Shares']
        result['stake_before'] = stake_before
        result['is_first_purchase'] = int(stake_before == 0)
        result['pct_added'] = row['Shares'] / stake_before if stake_before > 0 else None
        result['purchase_value'] = row['Shares'] * row['Price']
        result['filing_lag'] = (pd.to_datetime(row['filing_date']) - pd.to_datetime(row['Date'])).days

        pd.DataFrame([result]).to_csv(
            'returns_analysis.csv',
            mode = 'a',
            header = not os.path.exists('returns_analysis.csv'),
            index = False
        )
        results += 1
        
    else:
        error_counts[status] += 1
        

    
    if n % 100 == 0:
        print(f"{n} total rows evaluated | {results} results written | {dict(error_counts)}")

#clean the data up

df = pd.read_csv('returns_analysis.csv')

df_filtered = df[
    (df['purchase_value'] > 1000) &
    (df['Shares'] > 10) &
    (df['pct_added'] > 0.001) &
    (df['TransactionType'] == 'Purchase') &
    (df['EquitySwap'] == False) &
    (df['form'] == 4) &
    (df['filing_lag'] <= 5)
]

df_filtered.to_csv('returns_analysis_filtered.csv', index = False)