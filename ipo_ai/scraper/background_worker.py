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
    Runs the scraper in a background loop with a duty cycle:
    5 minutes of scraping (or until completion) then 2 minutes of rest.
    """
    logger.info("Starting Automated IPO Background Scraper Worker")
    logger.info("Cycle: 5 minutes ACTIVE / 2 minutes REST")
    
    while True:
        try:
            active_start = datetime.utcnow()
            logger.info(f"--- ACTIVE CYCLE START at {active_start.strftime('%Y-%m-%d %H:%M:%S UTC')} ---")
            
            # Run the scraper
            # Note: scrape_ipos takes a few seconds to a minute depending on network/driver speed
            scrape_ipos()
            
            # Calculate remaining time in the 5-minute active window if we want to BE active for 5 mins
            # But the user asked for "5 min scraping then 2 min rest". 
            # If scraping finishes early, we wait until the 5-minute mark to start resting? 
            # Or just scrape once and rest 2 mins? 
            # "5 min scraping" implies it should probably loop or just do one thorough pass.
            # Let's do one thorough pass, then ensure at least 5 minutes passed since start, then rest 2 mins.
            
            elapsed = (datetime.utcnow() - active_start).total_seconds()
            logger.info(f"Scraping pass completed in {elapsed:.2f} seconds.")
            
            # User specifically asked for: "5 min scraping then 2 min rest"
            # If scraping took less than 5 mins, we can just wait the rest of the 5 mins.
            if elapsed < 300:
                wait_to_rest = 300 - elapsed
                logger.info(f"Waiting {wait_to_rest:.2f}s to complete 5-minute active window...")
                time.sleep(wait_to_rest)
            
            logger.info("--- REST CYCLE START (2 Minutes) ---")
            time.sleep(120) # 2 minutes rest
            
            logger.info("--- CYCLE COMPLETE. Restarting... ---")
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in background worker loop: {e}")
            logger.info("Resting for 30s before retry...")
            time.sleep(30)

if __name__ == "__main__":
    run_background_scraper()
