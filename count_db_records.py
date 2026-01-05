from ipo_ai.db.database import engine, SessionLocal
from sqlalchemy import inspect, text

def count_records():
    session = SessionLocal()
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("=" * 50)
        print("DATABASE RECORD COUNT")
        print("=" * 50)
        print(f"\nDatabase: ipo_database.db")
        print(f"Total Tables: {len(tables)}\n")
        
        total_records = 0
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            total_records += count
            print(f"  {table}: {count} records")
        
        print("\n" + "=" * 50)
        print(f"TOTAL RECORDS ACROSS ALL TABLES: {total_records}")
        print("=" * 50)
        
    finally:
        session.close()

if __name__ == "__main__":
    count_records()
