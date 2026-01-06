import time
import logging
import sys
import os
from datetime import datetime as dt

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipo_ai.scraper.ipo_scraper import scrape_ipos
from ipo_ai.utils.logger import setup_logger

logger = setup_logger("background_worker")

def run_background_scraper():
    """
    Runs the scraper continuously without rest periods.
    """
    logger.info("Starting Automated IPO Background Scraper Worker")
    logger.info("Mode: CONTINUOUS SCRAPING (no rest periods)")
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            cycle_start = dt.utcnow()
            logger.info(f"--- SCRAPE CYCLE #{cycle_count} START at {cycle_start.strftime('%Y-%m-%d %H:%M:%S UTC')} ---")

            # Run the scraper
            scrape_ipos()

            elapsed = (dt.utcnow() - cycle_start).total_seconds()
            logger.info(f"Scraping cycle #{cycle_count} completed in {elapsed:.2f} seconds.")
            
            # Brief pause between cycles to avoid overwhelming the system
            logger.info("Starting next cycle immediately...")
            time.sleep(1)  # 1 second pause between cycles
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in background worker loop: {e}")
            logger.info("Resting for 30s before retry...")
            time.sleep(30)

if __name__ == "__main__":
    run_background_scraper()
