
import pandas as pd
import time
import os

from edgar import set_identity
set_identity("david lee absurdprofessor@gmail.com")

from edgar import Company, get_filings

#get filings for specific date range

def get_edgar_filings(): #get the filings we need to then parse and pull the form4 data

    filings = get_filings(form = "4", filing_date = "2023-01-01:2026-06-30") #adjust the date 

    tickers = pd.read_csv('tickers.csv') 
    tickerList = [tickers['Symbol'].iloc[i] for i in range(len(tickers))]#list of sp500 tickers

    sp500Filings = filings.filter(ticker = tickerList)

    #output = sp500Filings(filing_date = "2025-01-01:2025-12-31")

    return sp500Filings 

def get_form4(filings_list):
    all_purchases = []
    n = 0
    errors = 0
    p = 0
    if os.path.exists("insider_purchases_2025.csv"):
        os.remove("insider_purchases_2025.csv")
        
    for f in filings_list:
        n += 1
        time.sleep(0.15)
        try:
            form4 = f.obj()
            raw = form4.common_stock_purchases
            #print(f"Purchases: {purchases}")
            if raw is not None and len(raw) > 0:
                purchases = raw.copy()
                owner = form4.reporting_owners.owners[0] if form4.reporting_owners.owners else None
                purchases['insider_name'] = owner.name if owner else None
                purchases['officer_title'] = owner.officer_title if owner else None
                purchases['is_officer'] = owner.is_officer if owner else None
                purchases['is_director'] = owner.is_director if owner else None
                purchases['is_ten_pct_owner'] = owner.is_ten_pct_owner if owner else None
                purchases['ticker'] = form4.issuer.ticker
                purchases['company'] = form4.issuer.name
                purchases['filing_date'] = f.filing_date
                purchases['footnotes'] = form4.footnotes.text
                
                
                purchases.to_csv(
                    "insider_purchases_2025.csv",
                    mode = 'a',
                    header = not os.path.exists("insider_purchases_2025.csv"),
                    index = False)
                p += 1
                
        except Exception as e:
            errors += 1
            print(f"Error {e}")
            continue
            
        
        if n % 100 == 0:
            print(f"{n} filings processed | {p} purchases written | {errors} errors")

if __name__ == "__main__":
    filings = get_edgar_filings()
    get_form4(filings)