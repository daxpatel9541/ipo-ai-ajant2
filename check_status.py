import sqlite3

conn = sqlite3.connect('ipo_database.db')
cursor = conn.cursor()

cursor.execute("SELECT status, COUNT(*) FROM ipo_master GROUP BY status")
results = cursor.fetchall()

print("Status counts:")
for status, count in results:
    print(f"  {status}: {count}")

total = sum(count for _, count in results)
print(f"  Total: {total}")

conn.close()
