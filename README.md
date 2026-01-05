# Real-Time IPO Information AI

A production-ready AI system that tracks Indian IPOs, predicts listing gains, and recommends application categories.

## Features
*   **Automated Scraping**: Fetches IPO data (GMP, Subscription) every 2 hours.
*   **Machine Learning**:
    *   `RandomForestRegressor` for Listing Gain %.
    *   `RandomForestClassifier` for Best Category (Retail/HNI/QIB).
    *   Auto-retrains daily on new data.
*   **API**: FastAPI backend serving predictions.
*   **Database**: SQLite (Production-ready schema compatible with MySQL/Postgres).

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r ipo_ai/requirements.txt
    ```

2.  **Run the Scraper (Initial Data Load)**:
    ```bash
    python -m ipo_ai.scraper.ipo_scraper
    ```
    *Check `ipo_ai/utils/logger.py` logs to verify data fetching.*

3.  **Train the Models (Initial)**:
    ```bash
    python -m ipo_ai.training.auto_train
    ```
    *This will create `.pkl` files in the `models/` directory.*

4.  **Start the API Server**:
    ```bash
    uvicorn ipo_ai.api.main:app --reload
    ```
    *The server runs at `http://127.0.0.1:8000`.*
    *Swagger UI: `http://127.0.0.1:8000/docs`*

## API Usage

**Get IPO Details & Prediction**:
```http
GET /ipo?name=Swiggy
```

**Response**:
```json
{
  "ipo_details": {
    "name": "Swiggy Limited",
    "status": "upcoming",
    "current_gmp": 120.0,
    "subscription": { ... }
  },
  "ai_analysis": {
    "predicted_gain": "15.40%",
    "recommended_category": "Retail",
    "ai_explanation": "..."
  },
  "disclaimer": "..."
}
```

## Project Structure
*   `scraper/`: Data ingestion.
*   `training/`: ML pipeline.
*   `api/`: Backend service.
*   `db/`: Database access.
*   `models/`: Saved ML models.

## Note on Scraper
The scraper is configured to target a generic structure resembling popular IPO portals. If the target website changes its layout, update `parse_ipo_data` in `scraper/ipo_scraper.py`.
