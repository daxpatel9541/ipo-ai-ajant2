import time
from datetime import datetime
from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster

def monitor_database():
    """Monitor database for new additions and report them."""
    print("🔍 Starting database monitor...")
    print("=" * 60)
    
    db = SessionLocal()
    initial_count = db.query(IPOMaster).count()
    print(f"Initial count: {initial_count} IPOs")
    print(f"Monitoring started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\nWatching for new data... (Press Ctrl+C to stop)\n")
    db.close()
    
    last_count = initial_count
    check_interval = 10  # Check every 10 seconds
    
    try:
        while True:
            time.sleep(check_interval)
            
            db = SessionLocal()
            current_count = db.query(IPOMaster).count()
            
            if current_count > last_count:
                new_records = current_count - last_count
                print(f"🎉 NEW DATA ADDED!")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Added: {new_records} new IPO(s)")
                print(f"   Total: {current_count} IPOs")
                
                # Show the newly added IPOs
                new_ipos = db.query(IPOMaster).order_by(IPOMaster.scraped_at.desc()).limit(new_records).all()
                print(f"\n   New IPO(s):")
                for ipo in new_ipos:
                    print(f"   - {ipo.ipo_name} ({ipo.status})")
                print("-" * 60 + "\n")
                
                last_count = current_count
            
            db.close()
            
    except KeyboardInterrupt:
        print("\n\n✋ Monitor stopped by user.")
        print(f"Final count: {last_count} IPOs")

if __name__ == "__main__":
    monitor_database()
