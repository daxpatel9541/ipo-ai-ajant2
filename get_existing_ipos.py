import json
import os
import sys

# Add project root to path to import ipo_ai
sys.path.append(os.getcwd())

from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster

def get_existing_names():
    db = SessionLocal()
    try:
        db_names = [i.ipo_name for i in db.query(IPOMaster.ipo_name).all()]
    finally:
        db.close()
    
    h_path = os.path.join('ipo_ai', 'scraper', 'historical_data.json')
    h_names = []
    if os.path.exists(h_path):
        with open(h_path, 'r') as f:
            try:
                data = json.load(f)
                h_names = [i['ipo_name'] for i in data]
            except json.JSONDecodeError:
                pass
                
    all_names = list(set(db_names + h_names))
    return all_names

if __name__ == "__main__":
    names = get_existing_names()
    print(f"TOTAL_EXISTING:{len(names)}")
    # Print first 20 names for verification
    for name in names[:20]:
        print(f"EXISTING:{name}")
