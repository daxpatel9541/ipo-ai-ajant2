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
    return ipos

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
