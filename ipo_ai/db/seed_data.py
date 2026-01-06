import json
import os
import logging
from datetime import datetime
from ipo_ai.db.database import SessionLocal, engine, Base
from ipo_ai.db.models import IPOMaster

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_seeder")

def seed_data():
    logger.info("Database seeding disabled - only real scraped data allowed.")
    return

if __name__ == "__main__":
    seed_data()
