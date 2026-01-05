from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster
import requests
import json

def test_dual_logic():
    db = SessionLocal()
    
    # 1. Test Upcoming IPO
    print("--- Testing Upcoming IPO (Yajur) ---")
    ipo = db.query(IPOMaster).filter(IPOMaster.ipo_name.ilike("%Yajur%")).first()
    if ipo:
        ipo.status = "upcoming"
        db.commit()
    
    try:
        response = requests.get("http://127.0.0.1:8000/ipo?name=Yajur")
        data = response.json()
        print(f"Status: {data['ipo_details']['status']}")
        print(f"AI Analysis: {json.dumps(data['ai_analysis'], indent=2)}")
        if 'recommended_category' in data['ai_analysis'] and 'investment_advice' not in data['ai_analysis']:
            print("SUCCESS: Showed category for upcoming IPO.")
        else:
            print("FAILURE: Incorrect fields for upcoming IPO.")
    except Exception as e:
        print(f"Error testing upcoming: {e}")

    # 2. Test Listed IPO
    print("\n--- Testing Listed IPO (Apollo) ---")
    ipo = db.query(IPOMaster).filter(IPOMaster.ipo_name.ilike("%Apollo%")).first()
    if ipo:
        ipo.status = "listed"
        ipo.listing_gain = 16.88
        db.commit()
    
    try:
        response = requests.get("http://127.0.0.1:8000/ipo?name=Apollo")
        data = response.json()
        print(f"Status: {data['ipo_details']['status']}")
        print(f"AI Analysis: {json.dumps(data['ai_analysis'], indent=2)}")
        if 'investment_advice' in data['ai_analysis'] and 'recommended_category' not in data['ai_analysis']:
            print("SUCCESS: Showed investment advice for listed IPO.")
        else:
            print("FAILURE: Incorrect fields for listed IPO.")
    except Exception as e:
        print(f"Error testing listed: {e}")

    db.close()

if __name__ == "__main__":
    test_dual_logic()
