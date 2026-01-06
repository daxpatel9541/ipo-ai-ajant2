from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
import os
import glob
import joblib
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager
from typing import Optional

from ..db.database import get_db, Base, engine
from ..db.models import IPOMaster
from ..db.sync import sync_all_sources
from ..scraper.ipo_scraper import scrape_ipos
from ..training.auto_train import preprocess_and_train
from ..utils.logger import setup_logger

logger = setup_logger("api")

MODELS_DIR = "models"

# Helper to find latest model
def load_latest_model(prefix):
    files = glob.glob(f"{MODELS_DIR}/{prefix}_*.pkl")
    if not files:
        return None
    latest_file = max(files, key=os.path.getctime)
    logger.info(f"Loading model: {latest_file}")
    return joblib.load(latest_file)

def load_static_model(filename):
    path = f"{MODELS_DIR}/{filename}"
    if os.path.exists(path):
        return joblib.load(path)
    return None

ml_components = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up API...")
    
    # Initialize DB tables and Sync Data
    Base.metadata.create_all(bind=engine)
    sync_all_sources()
    
    # Scheduler (only for training, scraping is now continuous via background worker)
    scheduler = BackgroundScheduler()
    scheduler.add_job(preprocess_and_train, 'interval', hours=24)
    scheduler.start()
    logger.info("Scheduler started (training only - scraping is continuous).")

    # Load initial models (if any)
    try:
        ml_components['gain_model'] = load_latest_model("ipo_gain")
        ml_components['category_model'] = load_latest_model("ipo_category")
        ml_components['imputer'] = load_static_model("imputer.pkl")
        ml_components['encoder'] = load_static_model("category_encoder.pkl")
    except Exception as e:
        logger.error(f"Error loading models on startup: {e}")

    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("Shutting down.")

app = FastAPI(title="IPO AI API", lifespan=lifespan)

# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Mount static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/api/ipos")
def get_ipos(status: Optional[str] = None, name: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch IPO records from the database, optionally filtered by status or name, sorted by date."""
    query = db.query(IPOMaster)

    # Filter by status if provided
    if status:
        query = query.filter(IPOMaster.status == status)

    # Filter by name if provided (case-insensitive partial match)
    if name:
        query = query.filter(IPOMaster.ipo_name.ilike(f"%{name}%"))

    ipos = query.order_by(IPOMaster.scraped_at.desc()).all()

    # Return IPO details with only allowed fields
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

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ipos")
def get_all_ipos(db: Session = Depends(get_db)):
    # Fetch all IPOs from DB
    ipos = db.query(IPOMaster).all()

    # Convert to list of dicts
    ipo_list = []
    for ipo in ipos:
        ipo_list.append({
            "id": ipo.id,
            "name": ipo.ipo_name,
            "status": ipo.status,
            "issue_size": ipo.issue_size,
            "price_high": ipo.price_high,
            "gmp": ipo.gmp,
            "listing_gain": ipo.listing_gain,
            "retail_sub": ipo.retail_sub,
            "hni_sub": ipo.hni_sub,
            "qib_sub": ipo.qib_sub,
            "listing_date": ipo.listing_date.isoformat() if ipo.listing_date else None,
            "best_category": ipo.best_category
        })

    return {"ipos": ipo_list}

@app.get("/ipo")
def get_ipo_info(name: str, db: Session = Depends(get_db)):
    # Fetch IPO from DB
    ipo_record = db.query(IPOMaster).filter(IPOMaster.ipo_name.ilike(f"%{name}%")).first()

    if not ipo_record:
        raise HTTPException(status_code=404, detail="IPO not found in database. Please wait for the scraper to pick it up.")

    # Return only allowed fields, with "N/A" for missing values
    return {
        "ipo_name": ipo_record.ipo_name or "N/A",
        "status": ipo_record.status or "N/A",
        "gmp": ipo_record.gmp if ipo_record.gmp is not None else "N/A",
        "price_high": ipo_record.price_high if ipo_record.price_high is not None else "N/A",
        "issue_size": ipo_record.issue_size if ipo_record.issue_size is not None else "N/A",
        "retail_subscription": ipo_record.retail_sub if ipo_record.retail_sub is not None else "N/A",
        "hni_subscription": ipo_record.hni_sub if ipo_record.hni_sub is not None else "N/A",
        "qib_subscription": ipo_record.qib_sub if ipo_record.qib_sub is not None else "N/A",
        "listing_gain": ipo_record.listing_gain if ipo_record.listing_gain is not None else "N/A",
        "best_category": ipo_record.best_category or "N/A"
    }
