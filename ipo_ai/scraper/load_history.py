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
    print("Historical data loading disabled - only real scraped data allowed.")
    return

if __name__ == "__main__":
    load_historical_data()
