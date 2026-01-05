from ipo_ai.db.database import SessionLocal
from ipo_ai.db.models import IPOMaster

def list_all_ipos():
    """List all IPO names in the database."""
    db = SessionLocal()
    try:
        ipos = db.query(IPOMaster).order_by(IPOMaster.ipo_name).all()
        
        print("=" * 80)
        print(f"ALL IPOs IN DATABASE ({len(ipos)} total)")
        print("=" * 80)
        print()
        
        # Group by status
        upcoming = [ipo for ipo in ipos if ipo.status == "upcoming"]
        listed = [ipo for ipo in ipos if ipo.status == "listed"]
        open_ipos = [ipo for ipo in ipos if ipo.status == "open"]
        
        if listed:
            print(f"📊 LISTED IPOs ({len(listed)}):")
            print("-" * 80)
            for i, ipo in enumerate(listed, 1):
                size = f"₹{ipo.issue_size} Cr" if ipo.issue_size else "N/A"
                price = f"₹{ipo.price_high}" if ipo.price_high else "N/A"
                gain = f"{ipo.listing_gain}%" if ipo.listing_gain else "N/A"
                print(f"{i:2}. {ipo.ipo_name}")
                print(f"    Size: {size} | Price: {price} | Gain: {gain}")
            print()
        
        if open_ipos:
            print(f"🟢 OPEN IPOs ({len(open_ipos)}):")
            print("-" * 80)
            for i, ipo in enumerate(open_ipos, 1):
                size = f"₹{ipo.issue_size} Cr" if ipo.issue_size else "N/A"
                price = f"₹{ipo.price_high}" if ipo.price_high else "N/A"
                print(f"{i:2}. {ipo.ipo_name}")
                print(f"    Size: {size} | Price: {price}")
            print()
        
        if upcoming:
            print(f"🔜 UPCOMING IPOs ({len(upcoming)}):")
            print("-" * 80)
            for i, ipo in enumerate(upcoming, 1):
                size = f"₹{ipo.issue_size} Cr" if ipo.issue_size else "N/A"
                price = f"₹{ipo.price_high}" if ipo.price_high else "N/A"
                print(f"{i:2}. {ipo.ipo_name}")
                print(f"    Size: {size} | Price: {price}")
            print()
        
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    list_all_ipos()
