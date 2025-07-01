import logging
import random
import time
import os
from fake_useragent import UserAgent
import requests

DEBUG = True

# Setup logger
logger_dir = "./logger"
os.makedirs(logger_dir, exist_ok=True)
log_file = os.path.join(logger_dir, "extract_zomator_htmls.log")
logging.basicConfig(
    filename=log_file,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.DEBUG if DEBUG else logging.INFO
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

def get_random_headers():
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.zomato.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Origin": "https://www.zomato.com",
        "Cache-Control": "max-age=0",
        "TE": "Trailers",
        "Cookie": f"sessionid={random.randint(100000,999999)}; _ga={random.random()};"
    }
    # Randomize header order
    items = list(headers.items())
    random.shuffle(items)
    return dict(items)

def random_sleep(min_sec=1.5, max_sec=4.0):
    t = random.uniform(min_sec, max_sec)
    if DEBUG:
        logger.debug(f"Sleeping for {t:.2f} seconds to mimic human behavior...")
        print(f"[DEBUG] Sleeping for {t:.2f} seconds to mimic human behavior...")
    time.sleep(t)

def fetch_page(url, session):
    try:
        headers = get_random_headers()
        random_sleep()
        logger.info(f"Fetching: {url}")
        print(f"Fetching: {url}")
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        print(f"[ERROR] Request failed: {e}")
        return None

def save_content(content, path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        logger.info(f"Content saved to {path}")
        print(f"Content saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save content: {e}")
        print(f"[ERROR] Failed to save content: {e}")
