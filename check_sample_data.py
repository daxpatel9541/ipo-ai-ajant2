import sqlite3

conn = sqlite3.connect('ipo_database.db')
cursor = conn.cursor()

# Get sample data
cursor.execute("SELECT ipo_name, status, gmp, issue_size, price_high FROM ipo_master LIMIT 10")
rows = cursor.fetchall()

print("Sample IPO data:")
for row in rows:
    print(f"Name: {row[0][:40]}, Status: {row[1]}, GMP: {row[2]}, Size: {row[3]}, Price: {row[4]}")

conn.close()
