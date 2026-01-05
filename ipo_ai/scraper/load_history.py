import json
import os
from sqlalchemy.orm import Session
from ..db.database import SessionLocal, engine, Base
from ..db.models import IPOMaster
from datetime import datetime

# Helper to clean currency string
def clean_currency(val):
    if not val or val == "N/A": return 0.0
    return float(str(val).replace(',', '').replace('%', '').replace('Cr', '').strip())

def load_historical_data():
    file_path = os.path.join(os.path.dirname(__file__), 'historical_data.json')
    if not os.path.exists(file_path):
        print("Historical data file not found.")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    db: Session = SessionLocal()
    try:
        count = 0
        for item in data:
            name = item['ipo_name']
            existing = db.query(IPOMaster).filter(IPOMaster.ipo_name == name).first()
            
            # Parsing values
            gain = clean_currency(item.get('listing_gain'))
            size = clean_currency(item.get('issue_size'))
            price = clean_currency(item.get('issue_price')) # using issue price as price_high proxy if band not known
            
            if existing:
                existing.listing_gain = gain
                existing.status = 'listed'
                # Update others if missing
                if not existing.issue_size: existing.issue_size = size
                if not existing.price_high: existing.price_high = price
            else:
                new_ipo = IPOMaster(
                    ipo_name=name,
                    gmp=0.0, # Past data often doesn't have GMP record unless scraped from archive
                    retail_sub=0.0,
                    hni_sub=0.0,
                    qib_sub=0.0,
                    issue_size=size,
                    price_high=price,
                    listing_gain=gain,
                    status='listed',
                    scraped_at=datetime.utcnow()
                )
                db.add(new_ipo)
                count += 1
        
        db.commit()
        print(f"Successfully loaded {count} new historical records and updated existing ones.")
        
    except Exception as e:
        print(f"Error loading historical data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_historical_data()
