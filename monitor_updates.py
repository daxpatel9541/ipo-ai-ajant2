import time
from datetime import datetime
from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster

def monitor_database():
    """Monitor database for new additions and updates based on scraped_at changes."""
    print("Starting database monitor...")
    print("=" * 60)
    
    db = SessionLocal()
    initial_count = db.query(IPOMaster).count()
    # Get the latest scraped_at timestamp
    latest_scraped = db.query(IPOMaster.scraped_at).order_by(IPOMaster.scraped_at.desc()).first()
    last_scraped_at = latest_scraped[0] if latest_scraped else None
    
    print(f"Initial count: {initial_count} IPOs")
    print(f"Last scraped at: {last_scraped_at}")
    print(f"Monitoring started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\nWatching for new data and updates... (Press Ctrl+C to stop)\n")
    db.close()
    
    last_count = initial_count
    check_interval = 10  # Check every 10 seconds
    
    try:
        while True:
            time.sleep(check_interval)
            
            db = SessionLocal()
            current_count = db.query(IPOMaster).count()
            # Get the latest scraped_at timestamp
            latest_scraped = db.query(IPOMaster.scraped_at).order_by(IPOMaster.scraped_at.desc()).first()
            current_scraped_at = latest_scraped[0] if latest_scraped else None
            
            new_activity = False
            
            # Check for new IPOs
            if current_count > last_count:
                new_records = current_count - last_count
                print(f"🎉 NEW IPOS ADDED!")
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
                new_activity = True
            
            # Check for updates to existing IPOs
            elif current_scraped_at and last_scraped_at and current_scraped_at > last_scraped_at:
                print(f"🔄 EXISTING IPOS UPDATED!")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Last update was at: {last_scraped_at}")
                print(f"   New update detected at: {current_scraped_at}")
                
                # Find recently updated IPOs (within the last check interval + some buffer)
                recently_updated = db.query(IPOMaster).filter(
                    IPOMaster.scraped_at > last_scraped_at
                ).order_by(IPOMaster.scraped_at.desc()).all()
                
                print(f"\n   Updated IPO(s):")
                for ipo in recently_updated:
                    print(f"   - {ipo.ipo_name} ({ipo.status}) - Updated at {ipo.scraped_at}")
                print("-" * 60 + "\n")
                
                last_scraped_at = current_scraped_at
                new_activity = True
            
            if not new_activity:
                # Optional: Show a heartbeat every few minutes
                pass
            
            db.close()
            
    except KeyboardInterrupt:
        print("\n\n✋ Monitor stopped by user.")
        print(f"Final count: {last_count} IPOs")

if __name__ == "__main__":
    monitor_database()
