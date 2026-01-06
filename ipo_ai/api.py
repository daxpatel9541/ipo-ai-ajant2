from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from .db.database import SessionLocal, get_db
from .db.models import IPOMaster
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="IPO Real-Time AI System")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ipos")
def get_ipos(db: Session = Depends(get_db)):
    """Fetch all IPO records from the database, sorted by date."""
    ipos = db.query(IPOMaster).order_by(IPOMaster.scraped_at.desc()).all()
    
    # Return ALL IPO details, excluding only internal database fields
    result = []
    for ipo in ipos:
        result.append({
            "ipo_name": ipo.ipo_name,
            "status": ipo.status,
            "gmp": ipo.gmp if ipo.gmp is not None else 0,
            "price_high": ipo.price_high if ipo.price_high is not None else None,
            "issue_size": ipo.issue_size if ipo.issue_size is not None else None,
            "retail_subscription": ipo.retail_sub if ipo.retail_sub is not None else None,
            "hni_subscription": ipo.hni_sub if ipo.hni_sub is not None else None,
            "qib_subscription": ipo.qib_sub if ipo.qib_sub is not None else None,
            "listing_gain": ipo.listing_gain if ipo.listing_gain is not None else None,
            "listing_date": ipo.listing_date.isoformat() if ipo.listing_date else None,
            "best_category": ipo.best_category if ipo.best_category else None
        })
    
    return result

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get quick stats about the database."""
    total = db.query(IPOMaster).count()
    upcoming = db.query(IPOMaster).filter(IPOMaster.status == "upcoming").count()
    listed = db.query(IPOMaster).filter(IPOMaster.status == "listed").count()
    return {
        "total_ipos": total,
        "upcoming": upcoming,
        "listed": listed,
        "last_sync": db.query(IPOMaster).order_by(IPOMaster.scraped_at.desc()).first().scraped_at if total > 0 else None
    }

# Mount static files for the dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
