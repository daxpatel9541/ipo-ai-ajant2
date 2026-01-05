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
    logger.info("Starting database seeding...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Load JSON data
        json_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "historical_data.json")
        if not os.path.exists(json_path):
            logger.error(f"File not found: {json_path}")
            return

        with open(json_path, 'r') as f:
            data = json.load(f)
            
        logger.info(f"Loaded {len(data)} records from JSON.")
        
        added_count = 0
        
        for item in data:
            name = item.get('ipo_name')
            if not name:
                continue
                
            # Check if exists
            existing = db.query(IPOMaster).filter(IPOMaster.ipo_name == name).first()
            if existing:
                logger.info(f"Skipping existing: {name}")
                continue
                
            # Parse numeric fields
            issue_size = 0.0
            size_str = item.get('issue_size', '0')
            # Remove ' Cr' and commas
            clean_size = ''.join(c for c in size_str if c.isdigit() or c == '.')
            if clean_size:
                issue_size = float(clean_size)
                
            price = 0.0
            price_str = str(item.get('issue_price', '0'))
            clean_price = ''.join(c for c in price_str if c.isdigit() or c == '.')
            if clean_price:
                price = float(clean_price)
                
            listing_gain = 0.0
            gain_str = str(item.get('listing_gain', '0'))
            clean_gain = ''.join(c for c in gain_str if c.isdigit() or c == '.' or c == '-')
            if clean_gain:
                listing_gain = float(clean_gain)

            # Heuristic for best_category
            best_cat = "Retail"
            if listing_gain > 20:
                best_cat = "QIB"
            elif listing_gain > 5:
                best_cat = "HNI"

            new_ipo = IPOMaster(
                ipo_name=name,
                issue_size=issue_size,
                price_high=price,
                listing_gain=listing_gain,
                best_category=best_cat,
                status=item.get('status', 'listed'),
                scraped_at=datetime.utcnow()
            )
            db.add(new_ipo)
            added_count += 1
            logger.info(f"Adding: {name}")
            
        db.commit()
        logger.info(f"Seeding complete. Added {added_count} new records.")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
