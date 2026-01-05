
import json
from datetime import datetime
from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster

def inject_data(data):
    db = SessionLocal()
    try:
        added_count = 0
        for item in data:
            name = item['name']
            # Check if exists
            existing = db.query(IPOMaster).filter(IPOMaster.ipo_name == name).first()
            if existing:
                print(f"Skipping existing: {name}")
                continue
            
            new_ipo = IPOMaster(
                ipo_name=name,
                issue_size=float(item['size']),
                price_high=float(item['price']),
                status="listed",
                scraped_at=datetime.utcnow()
            )
            db.add(new_ipo)
            added_count += 1
            print(f"Added: {name}")
        
        db.commit()
        print(f"Successfully injected {added_count} records.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    scraped_data = [
      {"name": "Modern Diagnostic & Research Centre Ltd. IPO", "price": 90.00, "size": 36.89},
      {"name": "E to E Transportation Infrastructure Ltd. IPO", "price": 174.00, "size": 84.22},
      {"name": "Apollo Techno Industries Ltd. IPO", "price": 130.00, "size": 47.96},
      {"name": "Bai Kakaji Polymers Ltd. IPO", "price": 186.00, "size": 105.17},
      {"name": "Admach Systems Ltd. IPO", "price": 239.00, "size": 42.60},
      {"name": "Nanta Tech Ltd. IPO", "price": 220.00, "size": 31.81},
      {"name": "Dhara Rail Projects Ltd. IPO", "price": 126.00, "size": 50.20},
      {"name": "Sundrex Oil Co.Ltd. IPO", "price": 86.00, "size": 32.24},
      {"name": "Shyam Dhani Industries Ltd. IPO", "price": 70.00, "size": 38.49},
      {"name": "Gujarat Kidney & Super Speciality Ltd. IPO", "price": 114.00, "size": 250.80}
    ]
    inject_data(scraped_data)
