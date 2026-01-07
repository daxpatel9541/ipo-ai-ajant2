import sqlite3
from datetime import datetime

conn = sqlite3.connect('ipo_database.db')
cursor = conn.cursor()

# Let's check if any IPOs have listing dates that are in the future
# This would indicate they are "open" for subscription

# First, let's see what columns are available
cursor.execute("PRAGMA table_info(ipo_master)")
columns = cursor.fetchall()
print("Table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check for any IPOs that might be "open" based on their name patterns
# Open IPOs typically have keywords like "IPO" at the end and recent dates

cursor.execute("SELECT ipo_name, scraped_at FROM ipo_master ORDER BY scraped_at DESC LIMIT 5")
recent = cursor.fetchall()
print("\nMost recently scraped IPOs:")
for row in recent:
    print(f"  {row[0]}: {row[1]}")

conn.close()
