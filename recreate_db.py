import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ipo_ai.db.database import Base, engine

def recreate_tables():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating new tables with updated schema...")
    Base.metadata.create_all(bind=engine)

    print("Database schema updated successfully!")

if __name__ == "__main__":
    recreate_tables()