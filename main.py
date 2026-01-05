import uvicorn
import threading
import time
import logging
from ipo_ai.api import app
from ipo_ai.scraper.background_worker import run_background_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_server")

def start_scraper():
    """Starts the scraper in a separate thread."""
    logger.info("Initializing background scraper thread...")
    # Add a small delay to let the server start first
    time.sleep(5)
    run_background_scraper()

if __name__ == "__main__":
    # 1. Start Scraper Bot in Background Thread
    scraper_thread = threading.Thread(target=start_scraper, daemon=True)
    scraper_thread.start()
    
    # 2. Start Web Server
    # Port 8000 is default, but we'll be explicit
    logger.info("Starting Web Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
