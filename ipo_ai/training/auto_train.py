import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
import joblib
import os
from datetime import datetime
from ..db.database import DATABASE_URL
from ..utils.logger import setup_logger

logger = setup_logger("training")

MODELS_DIR = "models"
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

def load_data():
    engine = create_engine(DATABASE_URL)
    query = "SELECT * FROM ipo_master WHERE status='listed'" # Only train on listed IPOs for gain
    # For full system we might want to train on all available data for category, but Gain implies 'listed'
    # Actually, user said "Train models using FULL DATASET (Historical + Newly scraped)".
    # But 'listing_gain' is only known for 'listed' IPOs. 
    # 'best_category' might be known or inferred. 
    # I will fetch all and filter in pandas.
    df = pd.read_sql("SELECT * FROM ipo_master", engine)
    return df

def preprocess_and_train():
    logger.info("Loading data from database...")
    df = load_data()
    
    if df.empty:
        logger.warning("No data found in database. Skipping training.")
        return

    # Filter for rows that have 'listing_gain' for the regressor
    reg_df = df.dropna(subset=['listing_gain'])
    
    if len(reg_df) < 5:
        logger.warning(f"Not enough data to train (Found {len(reg_df)} records). Needing at least 5.")
        return

    # Features
    feature_cols = ['gmp', 'retail_sub', 'hni_sub', 'qib_sub', 'issue_size', 'price_high']
    
    # Preprocessing
    # Impute missing feature values with 0 or mean
    imputer = SimpleImputer(strategy='mean')
    
    X_reg = reg_df[feature_cols]
    y_reg = reg_df['listing_gain']
    
    X_reg = imputer.fit_transform(X_reg)
    
    # Train Gain Model
    logger.info("Training Listing Gain Model...")
    reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
    reg_model.fit(X_reg, y_reg)
    
    # Train Category Model
    # Assuming 'best_category' is populated. If not, we can't train this.
    # Logic: if 'best_category' is null, we might skip.
    class_df = df.dropna(subset=['best_category'])
    if not class_df.empty:
        logger.info("Training Best Category Model...")
        X_class = class_df[feature_cols]
        y_class = class_df['best_category']
        
        X_class = imputer.fit_transform(X_class) # Reuse/refit imputer? Better to fit new for this set
        
        le = LabelEncoder()
        y_class_enc = le.fit_transform(y_class)
        
        class_model = RandomForestClassifier(n_estimators=100, random_state=42)
        class_model.fit(X_class, y_class_enc)
        
        # Save Category models
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        joblib.dump(class_model, f"{MODELS_DIR}/ipo_category_{timestamp}.pkl")
        joblib.dump(le, f"{MODELS_DIR}/category_encoder.pkl") # generic name for latest? or versioned?
        # User asked for models/ipo_category_YYYYMMDD_HHMM.pkl and category_encoder.pkl
        # I'll save versioned and maybe symlink or just use logic to find latest.
        # User said "Uses the latest model".
        
    # Save Gain Models
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    joblib.dump(reg_model, f"{MODELS_DIR}/ipo_gain_{timestamp}.pkl")
    # Save imputer as well to handle new inputs? Good practice.
    joblib.dump(imputer, f"{MODELS_DIR}/imputer.pkl")

    logger.info(f"Training complete. Models saved to {MODELS_DIR}")

if __name__ == "__main__":
    preprocess_and_train()
