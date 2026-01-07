import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('ipo_database.db')
cursor = conn.cursor()

# Check for upcoming IPOs that might be open (based on various criteria)
# In India, IPOs typically open for 3-5 days for subscription
# We'll mark some upcoming IPOs as "open" if they have a price set but no listing date

# For now, let's manually check if there are any IPOs that should be open
# Based on current date (Jan 6, 2026), any upcoming IPO with a price should be checked

cursor.execute("SELECT ipo_name, status, price_high, gmp FROM ipo_master WHERE status='upcoming' AND price_high > 0")
upcoming_with_price = cursor.fetchall()

print(f"Upcoming IPOs with price: {len(upcoming_with_price)}")
for row in upcoming_with_price:
    print(f"  {row[0][:50]}: Price={row[2]}, GMP={row[3]}")

# Let's assume IPOs with price and GMP > 0 might be open for subscription
# This is a heuristic - in reality, we'd need better data from the websites

conn.close()
