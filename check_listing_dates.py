import sqlite3
from datetime import datetime

conn = sqlite3.connect('ipo_database.db')
cursor = conn.cursor()

# Check for IPOs with future listing dates
cursor.execute("SELECT ipo_name, listing_date, status FROM ipo_master WHERE listing_date IS NOT NULL ORDER BY listing_date DESC LIMIT 20")
rows = cursor.fetchall()

print("IPOs with listing dates:")
for row in rows:
    name = row[0][:40] if row[0] else 'N/A'
    listing_date = row[1]
    status = row[2]
    now = datetime.now()
    if listing_date:
        is_future = listing_date > now
        print(f"Name: {name}, Listing Date: {listing_date}, Status: {status}, Future: {is_future}")

conn.close()
