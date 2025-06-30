from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
import tempfile
import json
import re
import traceback

# Load environment variables from .env.development
load_dotenv('.env.development')

def create_stealth_driver():
    chrome_options = Options()

    # create unique temporary profile
    unique_prof_dir = tempfile.mkdtemp(prefix="chrome_profile_")
    chrome_options.add_argument(f"--user-data-dir={unique_prof_dir}")

    # essential chrome options
    # chrome_options.add_argument("--headless")  # Run Browser in headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    chrome_options.add_argument("--disablefeatures=VizDisplayCompositor")  # Disable VizDisplayCompositor
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_argument("--disable-plugins") # Disable plugins
    chrome_options.add_argument("--disable-images") # Disable images
    chrome_options.add_argument("--disable-notifications")  # Disable notifications
    chrome_options.add_argument("--disable-popup-blocking")  # Disable popup blocking

    # Advanced stealth options
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

   # Random realistic user-agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ] 

    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

    # Set window size to common resolution
    chrome_options.add_argument("--window-size=1920,1080")

    # Disable automation indicators
    chrome_options.add_experimental_option("detach", True)

    try:
        # Get ChromeDriver path from environment variable
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
        if not chromedriver_path:
            raise Exception("CHROMEDRIVER_PATH environment variable not set")
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Execute stealth scripts
        stealth_scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            "window.chrome = {runtime: {}}",
            "Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})})",
        ]

        for script in stealth_scripts:
            driver.execute_script(script)

        return driver
    except Exception as e:
        print(f"[ERROR] Failed to create driver: {e}")
        return None

def human_like_scroll(driver, pause_time=None):
    """Simulate human-like scrolling behavior"""
    if pause_time is None:
        pause_time = random.uniform(1, 3)

    # Get page height
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_height = 0

    while current_height < total_height:
        # Random scroll amount
        scroll_amount = random.randint(200, 600)
        current_height += scroll_amount

        driver.execute_script(f"window.scrollTo(0, {current_height});")
        time.sleep(random.uniform(0.5, 1.5))

        # Check if new content loaded
        new_total_height = driver.execute_script("return document.body.scrollHeight")
        if new_total_height > total_height:
            total_height = new_total_height
            time.sleep(pause_time)


def bypass_app_wall(driver):
    """Try to bypass app download/login prompts"""
    try:
        # Look for "Continue in browser" or similar buttons
        continue_selectors = [
            "//button[contains(text(), 'Continue in browser')]",
            "//a[contains(text(), 'Continue in browser')]",
            "//button[contains(text(), 'Skip')]",
            "//span[contains(text(), 'Continue in browser')]",
            "//div[contains(text(), 'Continue in browser')]",
        ]

        for selector in continue_selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                element.click()
                print(f"[DEBUG] Clicked 'Continue in browser' button")
                time.sleep(2)
                return True
            except TimeoutException:
                continue

        # Try pressing Escape key to close modals
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            print(f"[DEBUG] Pressed Escape to close modal")
            return True
        except:
            pass

    except Exception as e:
        print(f"[DEBUG] Error bypassing app wall: {e}")

    return False

# ---------------------------------------------
# RESTAURANT DATA LOADING
# ---------------------------------------------

def load_restaurant_data():
    """Load restaurant data from CSV file"""
    restaurants_csv = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/raw/zomato_restaurants.csv")
    )
    
    try:
        df = pd.read_csv(restaurants_csv)
        print(f"[DEBUG] Loaded {len(df)} restaurants from {restaurants_csv}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load restaurant data: {e}")
        return pd.DataFrame()

def extract_restaurant_info_from_url(url):
    """Extract restaurant slug and name from Zomato URL"""
    # URL format: https://www.zomato.com/pune/restaurant-slug/info
    if '/info' in url:
        url = url.replace('/info', '')
    
    parts = url.split('/')
    if len(parts) >= 4:
        city = parts[-2] if len(parts) >= 5 else 'pune'
        restaurant_slug = parts[-1]
        return city, restaurant_slug
    return None, None

# ---------------------------------------------
# MAIN SCRAPING LOGIC
# ---------------------------------------------

print("[DEBUG] Loading restaurant data...")
restaurant_df = load_restaurant_data()

if restaurant_df.empty:
    print("[ERROR] No restaurant data found. Exiting.")
    exit(1)

restaurants_to_scrape = restaurant_df.head(1)  # Take just one restaurant (the 1st one) 
print(f"[DEBUG] DEMO MODE: Will scrape just 1 restaurant for testing")

print(f"[DEBUG] Restaurants to scrape:")
for i, (idx, row) in enumerate(restaurants_to_scrape.iterrows()):
    print(f"  {i+1}. {row['name']}")

print("\n[DEBUG] Creating stealth driver...")
driver = create_stealth_driver()

# Ensure variables are always defined
df = pd.DataFrame()
all_reviews = []
csv_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/raw/zomato_reviews.csv")
)

if not driver:
    print("[ERROR] Failed to create driver. Exiting.")
    exit(1)

try:
    # Loop through restaurants
    for i, (rest_idx, rest_series) in enumerate(restaurants_to_scrape.iterrows()):
        rest_name = rest_series['name']
        rest_url = rest_series['url']

        print(f"\n[DEBUG] Scraping restaurant {i+1}: {rest_name} ({rest_url})")

        # Extract city and slug
        target_city, rest_slug = extract_restaurant_info_from_url(rest_url)

        if not target_city or not rest_slug:
            print(f"[ERROR] Invalid restaurant URL format: {rest_url}")
            continue

        base_url = f"https://www.zomato.com/{target_city}/{rest_slug}"

        print(f"[DEBUG] Visiting restaurant page: {base_url}")
        time.sleep(random.uniform(1, 3))
        bypass_app_wall(driver)

        # Navigate to reviews page
        reviews_url = f"{base_url}/reviews"
        print(f"[DEBUG] Navigating to reviews page: {reviews_url}")
        driver.get(reviews_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(random.uniform(2, 5))
        bypass_app_wall(driver)

        # --- Pagination Loop ---
        rest_reviews = []
        page_num = 1
        max_p = 3
        pagination_complete = False

        while page_num <= max_p and not pagination_complete:
            print(f"[DEBUG] Scraping reviews from page {page_num}...")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "section"))
                )
            except TimeoutException:
                print(f"[ERROR] Timeout while waiting for reviews on page {page_num}")

            time.sleep(random.uniform(2, 5))

            for scroll_attempt in range(1):
                try:
                    print(f"[DEBUG] Scrolling for more reviews (Attempt {scroll_attempt + 1})")
                    human_like_scroll(driver, pause_time=random.uniform(2, 4))
                    time.sleep(random.uniform(2, 5))
                except Exception as e:
                    print(f"[ERROR] Failed to scroll: {e}")
                    continue

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            review_sections = soup.find_all("section", class_="sc-cUbVUo cpuMVK")

            if not review_sections:
                print("[DEBUG] No review sections found.")
                pagination_complete = True
                break

            for section in review_sections:
                try:
                    restaurant_name = section.find('h2', class_='sc-dIn2kI-0 sc-tPTyfa jSVvMu')
                    review_container = section.find('div', class_='sc-eorICN fzFfPV')

                    if review_container:
                        reviewer = review_container.find('p', class_='sc-1hez2tp-0 sc-hOqGvO cSOZD')
                        rating = review_container.find('div', class_='sc-1q7bklc-1 cILgoX')
                        rating_type = review_container.find('div', class_='sc-1q7bklc-9 dRyijw')
                        review_age = review_container.find('div', class_='sc-1hez2tp-0 fkvqWN time-stamp')
                        review_text = review_container.find('p', class_='sc-1hez2tp-0 sc-iWdsYh bLBOqe')

                        rest_reviews.append({
                            'restaurant_name': restaurant_name.get_text(strip=True) if restaurant_name else rest_name,
                            'reviewer_name': reviewer.get_text(strip=True) if reviewer else None,
                            'rating': rating.get_text(strip=True) if rating else None,
                            'rating_type': rating_type.get_text(strip=True) if rating_type else None,
                            'review_age': review_age.get_text(strip=True) if review_age else None,
                            'review': review_text.get_text(strip=True) if review_text else None,
                        })
                except Exception as e:
                    print(f"[ERROR] Failed to extract review: {e}")
                    continue

            page_num += 1  # go to next page

        # ---- Convert to DataFrame and Save ----
        if rest_reviews:
            df = pd.DataFrame(rest_reviews)
            csv_filename = f"{rest_name.replace(' ', '_').lower()}_reviews.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"[INFO] Saved {len(df)} reviews to {csv_filename}")
        else:
            print(f"[INFO] No reviews scraped for {rest_name}")

except Exception as e:
    print(f"[ERROR] Error while scraping restaurant {i+1}: {e}")
    traceback.print_exc()