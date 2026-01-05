from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
import os
import glob
import joblib
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager

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
    
    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_ipos, 'interval', hours=2)
    scheduler.add_job(preprocess_and_train, 'interval', hours=24)
    scheduler.start()
    logger.info("Scheduler started.")

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

# Mount static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def home():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/ipo")
def get_ipo_info(name: str, db: Session = Depends(get_db)):
    # 1. Fetch IPO from DB
    ipo_record = db.query(IPOMaster).filter(IPOMaster.ipo_name.ilike(f"%{name}%")).first()
    
    if not ipo_record:
        # 404 if not in DB (Startup sync ensures JSON data is already indexed)
        raise HTTPException(status_code=404, detail="IPO not found in database. Please wait for the scraper to pick it up.")

    # 2. Prediction Preparation
    prediction_result = {
        "predicted_gain": None,
        "recommended_category": None,
        "investment_advice": None,
        "ai_explanation": "Models are not yet trained."
    }

    # Features: ['gmp', 'retail_sub', 'hni_sub', 'qib_sub', 'issue_size', 'price_high']
    features = pd.DataFrame([{
        'gmp': ipo_record.gmp if ipo_record.gmp else 0,
        'retail_sub': ipo_record.retail_sub if ipo_record.retail_sub else 0,
        'hni_sub': ipo_record.hni_sub if ipo_record.hni_sub else 0,
        'qib_sub': ipo_record.qib_sub if ipo_record.qib_sub else 0,
        'issue_size': ipo_record.issue_size if ipo_record.issue_size else 0,
        'price_high': ipo_record.price_high if ipo_record.price_high else 0
    }])

    # 3. Use Models
    if not ml_components.get('gain_model'):
        ml_components['gain_model'] = load_latest_model("ipo_gain")
        ml_components['imputer'] = load_static_model("imputer.pkl")
    
    if ml_components.get('gain_model') and ml_components.get('imputer'):
        try:
            imputed_features = ml_components['imputer'].transform(features)
            
            # Predict Gain
            gain_pred = ml_components['gain_model'].predict(imputed_features)[0]
            prediction_result['predicted_gain'] = f"{gain_pred:.2f}%"
            
            # 3.1 Branch Logic by Status
            if ipo_record.status == 'listed':
                # Listed IPO: Investment Advice
                gain = ipo_record.listing_gain if ipo_record.listing_gain is not None else gain_pred
                if gain > 50:
                    advice = "Profit Booking / Partial Sell recommended."
                elif gain > 0:
                    advice = "Hold for long-term growth or monitor trends."
                else:
                    advice = "Weak listing. Avoid or wait for price stabilization."
                
                prediction_result['investment_advice'] = advice
                prediction_result['ai_explanation'] = f"IPO listed with {gain:.2f}% gain. {advice}"
                # Hide category advice for listed
                prediction_result.pop('recommended_category', None)
            else:
                # Upcoming/Open IPO: Category Recommendation
                if not ml_components.get('category_model'):
                    ml_components['category_model'] = load_latest_model("ipo_category")
                    ml_components['encoder'] = load_static_model("category_encoder.pkl")
                    
                if ml_components.get('category_model'):
                    cat_pred_idx = ml_components['category_model'].predict(imputed_features)[0]
                    if ml_components.get('encoder'):
                        cat_pred_label = ml_components['encoder'].inverse_transform([cat_pred_idx])[0]
                        prediction_result['recommended_category'] = cat_pred_label
                
                prediction_result['ai_explanation'] = f"Based on GMP of {ipo_record.gmp} and subscription levels, the AI predicts a listing gain of approx {gain_pred:.2f}%. Recommended category to apply: {prediction_result.get('recommended_category')}."
                # Hide investment advice for upcoming
                prediction_result.pop('investment_advice', None)

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            prediction_result['ai_explanation'] = "Error generating prediction."

    # 4. Response
    return {
        "ipo_details": {
            "name": ipo_record.ipo_name,
            "status": ipo_record.status,
            "issue_size": ipo_record.issue_size,
            "price_band_high": ipo_record.price_high,
            "current_gmp": ipo_record.gmp,
            "listing_gain": ipo_record.listing_gain,
            "subscription": {
                "retail": ipo_record.retail_sub,
                "hni": ipo_record.hni_sub,
                "qib": ipo_record.qib_sub
            }
        },
        "ai_analysis": prediction_result,
        "disclaimer": "This is AI-based analysis, not financial advice. IPO allotment is not guaranteed."
    }
