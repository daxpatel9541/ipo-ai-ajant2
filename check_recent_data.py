from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster
from sqlalchemy import func
from datetime import datetime

def check_recent_data():
    session = SessionLocal()
    try:
        # Get total count
        total = session.query(func.count(IPOMaster.id)).scalar()
        
        print("=" * 70)
        print("IPO DATABASE ANALYSIS")
        print("=" * 70)
        print(f"\nTotal IPO Records: {total}")
        
        # Get most recent records
        recent = session.query(IPOMaster).order_by(IPOMaster.scraped_at.desc()).limit(10).all()
        
        if recent:
            print("\n" + "=" * 70)
            print("MOST RECENT 10 IPO RECORDS:")
            print("=" * 70)
            for idx, ipo in enumerate(recent, 1):
                print(f"\n{idx}. {ipo.ipo_name}")
                print(f"   Scraped At: {ipo.scraped_at}")
                print(f"   Status: {ipo.status}")
                if ipo.gmp:
                    print(f"   GMP: ₹{ipo.gmp}")
        
        # Check for records added today
        today = datetime.now().date()
        today_count = session.query(func.count(IPOMaster.id)).filter(
            func.date(IPOMaster.scraped_at) == today
        ).scalar()
        
        print("\n" + "=" * 70)
        print(f"Records Added Today ({today}): {today_count}")
        print("=" * 70)
        
        # Get all unique creation dates
        dates = session.query(
            func.date(IPOMaster.scraped_at).label('date'),
            func.count(IPOMaster.id).label('count')
        ).group_by(func.date(IPOMaster.scraped_at)).order_by('date').all()
        
        if dates:
            print("\n" + "=" * 70)
            print("RECORDS BY DATE:")
            print("=" * 70)
            for date, count in dates:
                print(f"  {date}: {count} records")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_recent_data()
