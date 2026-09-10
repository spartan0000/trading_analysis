# pipeline/run_daily.py
import logging
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PATH = Path(__file__).parent.parent
LOG_DIR = Path(os.environ.get("LOG_DIR", PATH / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / 'daily.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Import from all other modules
from pipeline.fetch_filings import get_new_filings
from pipeline.filters import apply_filters, passes_criteria, already_holding
from pipeline.regime import get_current_regime
from pipeline.alpaca_trader import execute_trade
from pipeline.position_manager import check_close_positions

def run():
    logging.info("=== Daily pipeline starting ===")
    
    try:
        # 1. Close any positions due first
        # Do this before buying so freed capital is available
        closed = check_close_positions()
        logging.info(f"Positions closed: {closed}")

        # 2. Get current market regime
        regime = get_current_regime()
        logging.info(f"Current regime: {regime}")

        # 3. Fetch new filings from EDGAR
        filings = get_new_filings()
        logging.info(f"New filings fetched: {len(filings)}")

        # 4. Apply primary filter stack
        signals = apply_filters(filings)
        logging.info(f"Signals after filter: {len(signals)}")

        if len(signals) == 0:
            logging.info("No signals today — done")
            return

        # 5. Get existing positions once
        existing_positions = already_holding()
        logging.info(f"Existing positions: {existing_positions}")

        # 6. Evaluate each signal and execute if criteria met
        executed = 0
        for _, signal in signals.iterrows():
            if passes_criteria(signal, regime, existing_positions):
                result = execute_trade(signal, regime)
                if result:
                    existing_positions.add(signal['ticker'])
                    executed += 1
            else:
                logging.info(f"Skipped {signal['ticker']} — criteria not met")

        logging.info(f"Trades executed: {executed}")

    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)

    finally:
        logging.info("=== Pipeline complete ===")

if __name__ == "__main__":
    run()