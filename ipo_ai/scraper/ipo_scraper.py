import logging
import time
import random
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from ..db.database import SessionLocal, engine, Base
from ..db.models import IPOMaster, IPOStatus
from ..utils.logger import setup_logger

logger = setup_logger("scraper")

# Ensure tables exist
Base.metadata.create_all(bind=engine)

import requests
from bs4 import BeautifulSoup
import json
import re
import yaml
import os

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    return session

def scrape_ipos(urls=None):
    all_data = []
    if not urls:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        sites = config['sites']
        urls = {site['name']: site['url'] for site in sites}
        
        # Expand URLs for Chittorgarh to include past years
        expanded_urls = {}
        for name, url in urls.items():
            if 'chittorgarh' in name.lower():
                current_year = datetime.now().year
                expanded_urls[f"{name} - All {current_year}"] = f"{url}/all/?year={current_year}"
                expanded_urls[f"{name} - Mainboard {current_year}"] = f"{url}/mainboard/?year={current_year}"
                expanded_urls[f"{name} - SME {current_year}"] = f"{url}/sme/?year={current_year}"
                for year in range(current_year - 1, current_year - 5, -1):  # last 4 years
                    expanded_urls[f"{name} - All {year}"] = f"{url}/all/?year={year}"
                    expanded_urls[f"{name} - Mainboard {year}"] = f"{url}/mainboard/?year={year}"
                    expanded_urls[f"{name} - SME {year}"] = f"{url}/sme/?year={year}"
            else:
                expanded_urls[name] = url
        urls = expanded_urls
    
    logger.info(f"Starting Selenium-based scraping for {len(urls)} URLs...")
    
    # Setup Selenium
    options = Options()
    options.add_argument("--headless")  # Run in background
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(10)
    
    total_new = 0
    total_updated = 0

    for category, url in urls.items():
        logger.info(f"Scraping category '{category}' from {url}...")
        try:
            driver.get(url)
            time.sleep(2)  # Wait for page to load
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 1. Try JSON extraction (__NEXT_DATA__)
            extracted_data = []
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            
            if next_data_script:
                try:
                    data = json.loads(next_data_script.string or "{}")
                    # Navigate the complex Next.js tree
                    props = data.get('props', {})
                    page_props = props.get('pageProps', {})
                    result_data = page_props.get('resultData', {})
                    report_data = result_data.get('reportData') or result_data.get('reportInfo') or []
                    
                    if not report_data:
                        # Sometimes it's in a different spot
                        report_data = result_data.get('reportItems') or []

                    for item in report_data:
                        name = item.get('company_name') or item.get('issuer_company_name') or item.get('ipo_name')
                        if not name: continue
                        
                        price = item.get('issue_price_rs') or item.get('issue_price') or item.get('price_high') or 0
                        size = item.get('total_issue_amount_rs_cr') or item.get('issue_size_cr') or item.get('size') or 0
                        
                        # Infer status
                        status = "listed" if "listed" in category else "upcoming"
                        raw_status = str(item.get('status', '')).lower()
                        if "listed" in raw_status: status = "listed"
                        elif "open" in raw_status: status = "open"
                        elif "closed" in raw_status: status = "listed"

                        extracted_data.append({
                            "ipo_name": name,
                            "issue_size": float(size) if size else 0.0,
                            "price_high": float(price) if price else 0.0,
                            "status": status,
                            "scraped_at": datetime.utcnow()
                        })
                except Exception as e:
                    logger.debug(f"JSON parse skipped for {category}")

            # 2. Table Fallback
            if not extracted_data:
                table = soup.find('table')
                if table:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        headers = [h.text.strip().lower() for h in rows[0].find_all(['th', 'td'])]
                        h_map = {
                            'name': next((i for i, h in enumerate(headers) if 'company' in h or 'issuer' in h), 0),
                            'price': next((i for i, h in enumerate(headers) if 'price' in h), -1),
                            'size': next((i for i, h in enumerate(headers) if 'size' in h), -1),
                            'status': next((i for i, h in enumerate(headers) if 'status' in h), -1)
                        }

                        for row in rows[1:]:
                            cols = row.find_all('td')
                            if not cols or len(cols) < 2: continue
                            try:
                                name = cols[h_map['name']].text.strip().split('\n')[0]
                                if not name: continue
                                
                                price_val = 0.0
                                if h_map['price'] != -1:
                                    p_txt = cols[h_map['price']].text.strip().split('-')[-1]
                                    p_cln = ''.join(c for c in p_txt if c.isdigit() or c == '.')
                                    if p_cln: price_val = float(p_cln)

                                size_val = 0.0
                                if h_map['size'] != -1:
                                    s_txt = cols[h_map['size']].text.strip()
                                    s_cln = ''.join(c for c in s_txt if c.isdigit() or c == '.')
                                    if s_cln: size_val = float(s_cln)

                                status = "listed" if "listed" in category else "upcoming"
                                if h_map['status'] != -1:
                                    st = cols[h_map['status']].text.strip().lower()
                                    if "listed" in st: status = "listed"
                                    elif "open" in st: status = "open"

                                extracted_data.append({
                                    "ipo_name": name,
                                    "issue_size": size_val,
                                    "price_high": price_val,
                                    "status": status,
                                    "scraped_at": datetime.utcnow()
                                })
                            except: continue

            if extracted_data:
                added, updated = save_to_db(extracted_data)
                total_new += added
                total_updated += updated
                all_data.extend(extracted_data)
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.error(f"Error scraping {category}: {e}")
    
    driver.quit()
    
    # Write all IPOs from DB to text file
    text_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ipo_data.txt')
    db: Session = SessionLocal()
    try:
        result = db.execute(text("SELECT ipo_name, issue_size, price_high, status, scraped_at FROM ipo_master ORDER BY scraped_at DESC")).fetchall()
        with open(text_file_path, 'w') as f:
            for row in result:
                f.write(f"IPO Name: {row[0]}, Issue Size: {row[1]}, Price: {row[2]}, Status: {row[3]}, Scraped At: {row[4]}\n")
    finally:
        db.close()
    
    logger.info(f"Full scrape cycle complete. Added: {total_new}, Updated: {total_updated}")

def save_to_db(data):
    if not data: return 0, 0
    db: Session = SessionLocal()
    new_count = 0
    update_count = 0
    try:
        for item in data:
            existing = db.query(IPOMaster).filter(IPOMaster.ipo_name == item['ipo_name']).first()
            if existing:
                for key, value in item.items():
                    if key != "ipo_name" and value is not None:
                        if isinstance(value, float) and value > 0:
                            setattr(existing, key, value)
                        elif isinstance(value, (str, datetime)):
                            setattr(existing, key, value)
                update_count += 1
            else:
                new_ipo = IPOMaster(**item)
                db.add(new_ipo)
                new_count += 1
        db.commit()
    except Exception as e:
        logger.error(f"DB Update Error: {e}")
        db.rollback()
    finally:
        db.close()
    return new_count, update_count

if __name__ == "__main__":
    scrape_ipos()
