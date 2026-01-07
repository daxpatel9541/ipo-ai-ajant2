import time
import logging
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ipo_ai.scraper.ipo_scraper import scrape_ipos
from ipo_ai.utils.logger import setup_logger

logger = setup_logger("background_worker")

def run_background_scraper():
    """
    Runs the scraper with 10 minutes scraping followed by 5 minutes break.
    """
    logger.info("Starting Automated IPO Background Scraper Worker")
    logger.info("Mode: 10 MIN SCRAPING + 5 MIN BREAK")

    cycle_count = 0

    while True:
        try:
            # Scraping phase: 10 minutes
            scraping_end = datetime.utcnow() + timedelta(minutes=10)
            logger.info(f"Starting scraping phase until {scraping_end.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            while datetime.utcnow() < scraping_end:
                cycle_count += 1
                cycle_start = datetime.utcnow()
                logger.info(f"--- SCRAPE CYCLE #{cycle_count} START at {cycle_start.strftime('%Y-%m-%d %H:%M:%S UTC')} ---")

                # Run the scraper
                scrape_ipos()

                elapsed = (datetime.utcnow() - cycle_start).total_seconds()
                logger.info(f"Scraping cycle #{cycle_count} completed in {elapsed:.2f} seconds.")

                # Brief pause between cycles
                time.sleep(1)

            # Break phase: 5 minutes
            break_end = datetime.utcnow() + timedelta(minutes=5)
            logger.info(f"Starting break phase until {break_end.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            time.sleep(300)  # 5 minutes

        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in background worker loop: {e}")
            logger.info("Resting for 30s before retry...")
            time.sleep(30)

if __name__ == "__main__":
    run_background_scraper()
