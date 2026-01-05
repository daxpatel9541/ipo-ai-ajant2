import json
import os
import logging
from datetime import datetime
from .database import SessionLocal, engine, Base
from .models import IPOMaster

logger = logging.getLogger("db_sync")

def sync_all_sources():
    """Synchronize all JSON files and other sources into the DB."""
    logger.info("Starting database synchronization...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Sync historical_data.json
        historical_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "historical_data.json")
        sync_json_file(db, historical_path)
        
        # 2. Sync cached_data.json
        cached_path = os.path.join(os.path.dirname(__file__), "..", "scraper", "cached_data.json")
        sync_json_file(db, cached_path)
        
        db.commit()
        logger.info("Synchronization complete.")
    except Exception as e:
        logger.error(f"Error during synchronization: {e}")
        db.rollback()
    finally:
        db.close()

def sync_json_file(db, file_path):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        logger.info(f"Syncing {len(data)} records from {os.path.basename(file_path)}...")
        
        added_count = 0
        update_count = 0
        for item in data:
            name = item.get('ipo_name')
            if not name:
                continue
                
            existing = db.query(IPOMaster).filter(IPOMaster.ipo_name == name).first()
            
            # Prepare fields
            issue_size = 0.0
            size_str = str(item.get('issue_size', '0'))
            clean_size = ''.join(c for c in size_str if c.isdigit() or c == '.')
            if clean_size: issue_size = float(clean_size)
                
            price = 0.0
            price_str = str(item.get('issue_price', item.get('price_high', '0')))
            clean_price = ''.join(c for c in price_str if c.isdigit() or c == '.')
            if clean_price: price = float(clean_price)
                
            gain = 0.0
            gain_str = str(item.get('listing_gain', '0'))
            clean_gain = ''.join(c for c in gain_str if c.isdigit() or c == '.' or c == '-')
            if clean_gain: gain = float(clean_gain)

            # Heuristic for best_category
            best_cat = item.get('best_category')
            if not best_cat:
                best_cat = "Retail"
                if gain > 20: best_cat = "QIB"
                elif gain > 5: best_cat = "HNI"

            if existing:
                # Update existing record (Upsert)
                if issue_size > 0: existing.issue_size = issue_size
                if price > 0: existing.price_high = price
                if gain != 0: existing.listing_gain = gain
                if item.get('status'): existing.status = item.get('status')
                if item.get('gmp'): existing.gmp = item.get('gmp')
                existing.scraped_at = datetime.utcnow()
                update_count += 1
            else:
                new_ipo = IPOMaster(
                    ipo_name=name,
                    gmp=item.get('gmp', 0.0),
                    retail_sub=item.get('retail_sub', 0.0),
                    hni_sub=item.get('hni_sub', 0.0),
                    qib_sub=item.get('qib_sub', 0.0),
                    issue_size=issue_size,
                    price_high=price,
                    listing_gain=gain,
                    best_category=best_cat,
                    status=item.get('status', 'listed')
                )
                db.add(new_ipo)
                added_count += 1
        
        logger.info(f"Sync complete for {os.path.basename(file_path)}. Added: {added_count}, Updated: {update_count}")
        
    except Exception as e:
        logger.error(f"Error syncing file {file_path}: {e}")

if __name__ == "__main__":
    # Setup simple logging for manual run
    logging.basicConfig(level=logging.INFO)
    sync_all_sources()
