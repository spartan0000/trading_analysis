import pandas as pd
from datetime import datetime, timedelta
from edgar import get_filings
import logging
from pathlib import Path
from pipeline.exceptions import FilingFetchError
from pipeline.regime import get_current_regime

PATH = Path(__file__).parent.parent

def get_new_filings():
    """Fetch Form 4 filings from the last business day"""
    
    yesterday = get_last_business_day()
    date_range = f"{yesterday}:{yesterday}"
    
    logging.info(f"Fetching Form 4 filings for {yesterday}")
    
    try:
        # Same pattern as existing script edgarForm4.py
        filings = get_filings(form="4", filing_date=date_range)
        
        # Filter to SP500 tickers
        tickers = pd.read_csv(PATH / 'data' / 'tickers.csv')
        ticker_list = tickers['Symbol'].tolist()
        sp500_filings = filings.filter(ticker=ticker_list)
        
        logging.info(f"SP500 Form 4 filings: {len(sp500_filings)}")
        
        # Parse each filing — same as your get_form4 function
        all_purchases = []
        errors = 0
        
        for f in sp500_filings:
            try:
                form4 = f.obj()
                raw = form4.common_stock_purchases
                
                if raw is None or len(raw) == 0:
                    continue
                
                purchases = raw.copy()
                owner = form4.reporting_owners.owners[0] if form4.reporting_owners.owners else None
                
                purchases['insider_name'] = owner.name if owner else None
                purchases['officer_title'] = owner.officer_title if owner else None
                purchases['is_officer'] = owner.is_officer if owner else False
                purchases['is_director'] = owner.is_director if owner else False
                purchases['is_ten_pct_owner'] = owner.is_ten_pct_owner if owner else False
                purchases['ticker'] = form4.issuer.ticker
                purchases['company'] = form4.issuer.name
                purchases['filing_date'] = f.filing_date

                all_purchases.append(purchases)
                
            except Exception as e:
                errors += 1
                logging.warning(f"Filing parse error: {e}")
                continue
        
        if not all_purchases:
            logging.info("No purchases found in today's filings")
            return pd.DataFrame()
        
        df = pd.concat(all_purchases, ignore_index=True)
        
        # Add derived columns — same as your existing pipeline
        df = add_derived_columns(df)
        
        logging.info(f"Parsed {len(df)} purchases, {errors} errors")
        return df
        
    except Exception as e:
        logging.error(f"Filing fetch failed: {e}")
        raise FilingFetchError(f"EDGAR API failed to return filings: {e}") from e
        #return pd.DataFrame()

def get_last_business_day():
    """Returns yesterday, or Friday if today is Monday"""
    today = datetime.now()
    if today.weekday() == 0:  # Monday
        return (today - timedelta(days=3)).strftime('%Y-%m-%d')
    else:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')

def add_derived_columns(df):
    """Add the same derived columns as your historical pipeline"""
    
    # Filing lag
    df['filing_date'] = pd.to_datetime(df['filing_date'])
    df['Date'] = pd.to_datetime(df['Date'])
    df['filing_lag'] = (df['filing_date'] - df['Date']).dt.days

    # form4.common_stock_purchases yields 'form' as a string ('4'); the filter
    # stack (passes_trade_criteria / apply_analysis_filters) compares it to the
    # int 4, so normalize here rather than leaving it to silently never match.
    df['form'] = df['form'].astype(int)
    
    # Purchase value
    if 'purchase_value' not in df.columns:
        df['purchase_value'] = df['Shares'] * df['Price']
    
    # Stake metrics
    df['stake_before'] = df['Remaining'] - df['Shares']
    df['pct_added'] = df['Shares'] / df['stake_before'].replace(0, float('nan'))
    
    # Role flags
    df['is_ceo'] = df['officer_title'].str.contains(
        'Chief Executive|CEO', case=False, na=False
    ).astype(int)
    df['is_non_ceo_officer'] = (
        df['is_officer'] & ~df['is_ceo'].astype(bool)
    ).astype(int)
    
    # First purchase flag
    df['is_first_purchase'] = False  # can't determine from single day pull - may just take this out since it was a weak signal anyway

    df['market_regime'] = get_current_regime()
    
    return df