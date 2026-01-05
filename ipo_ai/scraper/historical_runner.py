import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from ipo_ai.db.database import SessionLocal, engine, Base
from ipo_ai.db.models import IPOMaster

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("historical_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("historical_scraper")

import requests
from bs4 import BeautifulSoup

def scrape_historical(url, year_label, limit=10):
    logger.info(f"Starting historical scrape for {year_label} from {url} (Limit: {limit})")
    db = SessionLocal()
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        logger.info(f"Response status: {response.status_code}")
        response.raise_for_status()
        
        # Save to file for thorough inspection
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info("Saved page content to debug_page.html")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Next.js pages often store data in a script tag with id="__NEXT_DATA__"
        # Or in multiple scripts with self.__next_f.push([...])
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        report_data = []
        if next_data_script:
            import json
            logger.info("Found __NEXT_DATA__ script. Parsing JSON...")
            try:
                data = json.loads(next_data_script.string)
                props = data.get('props', {})
                page_props = props.get('pageProps', {})
                result_data = page_props.get('resultData', {})
                report_data = result_data.get('reportData') or result_data.get('reportInfo') or []
            except Exception as e:
                logger.error(f"Error parsing __NEXT_DATA__: {e}")

        if not report_data:
            logger.info("Iterating all script tags for discovery...")
            scripts = soup.find_all('script')
            for i, s in enumerate(scripts):
                script_id = s.get('id', 'No ID')
                content = s.string if s.string else ""
                snippet = content[:100].replace('\n', ' ')
                logger.info(f"Script {i} [id={script_id}]: {snippet}...")
                
                if "report" in content.lower() or "ipo" in content.lower() or "company" in content.lower():
                    logger.info(f"--- POTENTIAL DATA IN SCRIPT {i} ---")
                    # Try a very loose extraction
                    # Look for anything between { and } that contains company_name
                    import re
                    # Finding objects that contain "company_name" or "issuer_company_name"
                    obj_matches = re.finditer(r'\{[^{}]*company_name[^{}]*\}', content)
                    for mo in obj_matches:
                        try:
                            raw_obj = mo.group(0).replace('\\"', '"').replace('\\\\"', '"')
                            import json
                            record = json.loads(raw_obj)
                            if 'company_name' in record:
                                report_data.append(record)
                        except: continue
                if len(report_data) > 0:
                    logger.info(f"Successfully extracted {len(report_data)} records from script {i}")
                    break

        if report_data:
            logger.info(f"Successfully extracted {len(report_data)} items.")
            processed_count = 0
            for item in report_data:
                if processed_count >= limit:
                    break
                
                if not isinstance(item, dict): continue

                name = item.get('company_name') or item.get('issuer_company_name') or item.get('ipo_name') or item.get('report_name')
                if not name: continue
                
                existing = db.query(IPOMaster).filter(IPOMaster.ipo_name == name).first()
                if existing: continue
                
                # Extract fields
                price = item.get('issue_price_rs') or item.get('issue_price') or item.get('price') or 0
                if isinstance(price, str):
                    price = ''.join(c for c in price if c.isdigit() or c == '.')
                    price = float(price) if price else 0.0
                
                size = item.get('total_issue_amount_rs_cr') or item.get('issue_size') or item.get('size') or 0
                if isinstance(size, str):
                    size = ''.join(c for c in size if c.isdigit() or c == '.')
                    size = float(size) if size else 0.0
                
                new_ipo = IPOMaster(
                    ipo_name=name,
                    issue_size=float(size),
                    price_high=float(price),
                    status="listed",
                    scraped_at=datetime.utcnow()
                )
                db.add(new_ipo)
                db.commit()
                processed_count += 1
                logger.info(f"Added {processed_count}/{limit}: {name}")
            
            if processed_count > 0:
                logger.info(f"Completed. Added {processed_count} records.")
                return

        logger.error("All extraction methods failed.")
            
        # ... rest of the old table logic ...

    except Exception as e:
        logger.error(f"Global error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Scrape 10 IPOs from 2024 list
    scrape_historical("https://www.chittorgarh.com/report/ipo-in-india-list-main-board-sme/82/?year=2024", "2024", limit=10)
