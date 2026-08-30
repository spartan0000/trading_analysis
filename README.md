# Insider Purchase Analysis

Does insider buying in S&P 500 stocks beat the market?

- **edgarForm4.py** — pulls SEC Form 4 filings (via [edgartools](https://github.com/dgunning/edgartools)) for S&P 500 tickers and writes open-market purchases to `insider_purchases_2025.csv`.
- **edgarAnalysis.py** — for each purchase, computes the stock's 90-day return vs. SPY (alpha) using cached prices in `sp500_prices.parquet`, and writes results to `returns_analysis.csv`.
