from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
import tempfile
import json
import re
import traceback
from urllib.parse import urljoin

'''
Zomato Review Scraper (Phase 2)
===============================

This program is designed to scrape restaurant reviews from Zomato, with enhanced anti-detection
and data extraction capabilities. It supports both a demo mode for testing and a full mode for
comprehensive data collection.

Features:
---------
1. Stealth browser automation with randomized behavior to avoid detection
2. Multi-stage review extraction from both HTML and JSON-LD
3. Pagination handling to collect all reviews for each restaurant
4. Comprehensive data collection including:
   - Restaurant name
   - Reviewer name
   - Rating value (numerical)
   - Rating type (DINING or DELIVERY)
   - Review text
   - Date of review
5. Detection and handling of login/app walls
6. Robust error handling and debug information
7. Demo/Actual mode toggle for testing vs production use

Usage:
------
Set DEMO_MODE to True for limited testing (5 restaurants, limited reviews)
Set DEMO_MODE to False for full scraping (all restaurants, all reviews)

Data Flow:
---------
1. Load restaurant data from CSV
2. Initialize browser with anti-detection measures
3. For each restaurant:
   a. Visit main restaurant page
   b. Navigate to reviews section
   c. Extract reviews from each page
   d. Handle pagination until all reviews are collected or limits reached
4. Save collected reviews to CSV with metadata

Dependencies:
------------
- Selenium WebDriver
- BeautifulSoup4
- Pandas
- Chrome/Chromedriver

Author: Data Analysis Team
Version: 2.0
'''

# Configuration
DEMO_MODE = True  # Set to False for full scraping of all restaurants and all reviews

def create_stealth_driver():
    """Create a stealth Chrome driver with enhanced anti-detection measures"""
    chrome_options = Options()

    # Create unique temporary profile
    unique_profile_dir = tempfile.mkdtemp(prefix="chrome-profile-")
    chrome_options.add_argument(f"--user-data-dir={unique_profile_dir}")

    # Essential Chrome options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    # Advanced stealth options
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Random realistic user agent
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
        service = Service("/usr/bin/chromedriver")
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


def extract_reviews_from_json_ld(soup):
    """Extract reviews from JSON-LD structured data"""
    reviews = []
    try:
        # Find JSON-LD script tags containing restaurant data
        json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                # Check if this is restaurant data with reviews
                if isinstance(data, dict) and data.get('@type') == 'Restaurant' and 'reviews' in data:
                    for review_data in data.get('reviews', []):
                        rating_value = review_data.get('reviewRating', {}).get('ratingValue', 'N/A')
                        # Convert to string and ensure it's a valid format
                        rating = str(rating_value) if rating_value != 'N/A' else 'N/A'
                        
                        reviews.append({
                            'reviewer': review_data.get('author', 'N/A'),
                            'rating': rating,
                            'rating_type': 'DINING',  # Assume DINING as default for JSON-LD reviews
                            'review_text': review_data.get('description', 'N/A'),
                            'date': 'N/A',  # Not available in structured data
                            'extraction_method': 'json-ld'
                        })
                    
                    # Print debug info
                    print(f"[DEBUG] Successfully extracted {len(reviews)} reviews from JSON-LD data")
                    if reviews:
                        print(f"[DEBUG] Sample JSON-LD review: {reviews[0]}")
                        
                    break  # Found reviews, no need to check other scripts
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[DEBUG] Error parsing JSON-LD script: {e}")
                continue
                
    except Exception as e:
        print(f"[DEBUG] Error extracting from JSON-LD: {e}")
        
    return reviews


def extract_reviews_with_multiple_selectors(soup, restaurant_name="N/A"):
    """Try multiple CSS selectors to find reviews"""
    all_reviews = []
    
    # Save the soup for debugging if demo mode is enabled
    debug_dir = "data/raw/debug"
    os.makedirs(debug_dir, exist_ok=True)
    if DEMO_MODE:
        with open(f"{debug_dir}/full_review_page.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"Saved complete review page HTML to {debug_dir}/full_review_page.html for analysis")

        # --- ENHANCEMENT: Save Selenium outerHTML for first 3 review cards ---
        try:
            from selenium.webdriver.remote.webelement import WebElement
            # Try to get the Selenium driver from the global scope (hacky but works for debug)
            import builtins
            driver = getattr(builtins, 'selenium_driver', None)
            if driver:
                # Try common selectors for review cards
                review_card_selectors = [
                    "section[class*='ReviewCard']",
                    "div[class*='ReviewCard']",
                    "section.sc-dENsGg",
                    "div[data-testid='review-card']",
                    "section[class*='review']",
                    "div[class*='review']",
                    "article[class*='review']",
                    ".sc-dENsGg",
                    "section.sc-1q7bklc-0",
                    "div.review-container",
                    "div[class*='UserReview']",
                    "div[class*='ReviewLayout']",
                    "div[class*='sc-'][class*='Review']",
                ]
                found = False
                for sel in review_card_selectors:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    if elems:
                        print(f"[DEBUG] [Selenium] Found {len(elems)} review cards with selector: {sel}")
                        for i, elem in enumerate(elems[:3]):
                            outer_html = elem.get_attribute('outerHTML')
                            with open(f"{debug_dir}/selenium_review_section_{i+1}.html", "w", encoding="utf-8") as f:
                                f.write(outer_html)
                            print(f"[DEBUG] [Selenium] Saved review card {i+1} outerHTML to {debug_dir}/selenium_review_section_{i+1}.html")
                        found = True
                        break
                if not found:
                    print("[DEBUG] [Selenium] No review cards found for debug outerHTML saving.")
            else:
                print("[DEBUG] [Selenium] Driver not available for outerHTML debug saving.")
        except Exception as e:
            print(f"[DEBUG] [Selenium] Error saving review card outerHTML: {e}")

    # Multiple possible selectors for review containers (updated for current Zomato structure)
    review_selectors = [
        "section[class*='ReviewCard']",  # New common pattern
        "div[class*='ReviewCard']", 
        "section.sc-dENsGg",  # Legacy common review container
        "div[data-testid='review-card']",
        "section[class*='review']",
        "div[class*='review']",
        "article[class*='review']",
        ".sc-dENsGg",
        "section.sc-1q7bklc-0",
        "div.review-container",
        "div[class*='UserReview']",
        "div[class*='ReviewLayout']",
        "div[class*='sc-'][class*='Review']",  # Generic styled-components pattern
    ]

    print(f"[DEBUG] Trying {len(review_selectors)} different selectors...")

    for selector in review_selectors:
        review_sections = soup.select(selector)
        if review_sections:
            print(
                f"[DEBUG] Found {len(review_sections)} reviews with selector: {selector}"
            )

            # Save the first few review HTML snippets for debugging in demo mode
            if DEMO_MODE and review_sections:
                debug_dir = "data/raw/debug"
                os.makedirs(debug_dir, exist_ok=True)
                # Save up to 3 reviews for debugging
                for i, section in enumerate(review_sections[:3]):
                    with open(f"{debug_dir}/review_section_{i+1}.html", "w", encoding="utf-8") as f:
                        f.write(str(section))
                    print(f"Saved review section {i+1} HTML to {debug_dir}/review_section_{i+1}.html")

            for idx, section in enumerate(review_sections):
                try:
                    # Extract reviewer name (based on actual HTML structure)
                    reviewer_selectors = [
                        "p.sc-1hez2tp-0.sc-lenlpJ.dCAQIv",  # Specific class for reviewer names
                        "p.sc-1hez2tp-0.sc-lenlpJ",
                        "div.sc-kGYfcE div p",
                        "p[class*='reviewer']",
                        "span[class*='name']",
                        "div[class*='user-name']",
                        "h4",
                        "h5",
                        "h6",
                    ]

                    reviewer = "N/A"
                    for rev_sel in reviewer_selectors:
                        rev_elem = section.select_one(rev_sel)
                        if rev_elem and rev_elem.get_text(strip=True):
                            reviewer = rev_elem.get_text(strip=True)
                            break

                    # For this data, we're going to extract ratings from the HTML structure and JSON-LD data
                    # First try HTML extraction for ratings
                    rating = "N/A"
                    rating_type = "DINING"  # Default to DINING as it's most common

                    # APPROACH 1: Extract from specific rating-related elements
                    rating_selectors = [
                        "div[class*='rating']", "span[class*='rating']", 
                        "div[class*='star']", "span[class*='star']",
                        # Look for elements containing star symbols
                        "*:contains(★)", "*:contains(⭐)", "*:contains(☆)"
                    ]

                    for selector in rating_selectors:
                        try:
                            elements = section.select(selector)
                            for element in elements:
                                text = element.get_text(strip=True)
                                # Look for numbers in the text
                                numbers = re.findall(r'(\d+(\.\d+)?)', text)
                                if numbers:
                                    # Get the first number between 1-5
                                    for num in numbers:
                                        if 1 <= float(num[0]) <= 5:
                                            rating = num[0]
                                            break
                                    if rating != "N/A":
                                        break
                        except Exception:
                            continue
                            
                    # APPROACH 2: Look for SVG star icons which Zomato uses
                    if rating == "N/A":
                        try:
                            # Find all SVG elements that might represent stars
                            svg_stars = section.find_all('svg', {
                                'class': lambda x: x and ('star' in x.lower() if x else False)
                            }) or section.find_all('svg', {
                                'title': lambda x: x and ('star' in x.lower() if x else False)
                            })
                            
                            if svg_stars:
                                # Count the number of filled stars
                                filled_stars = []
                                for svg in svg_stars:
                                    # Check for attributes that might indicate a filled star
                                    # Filled stars often have different classes or fill attributes
                                    if svg.get('fill') and svg.get('fill') != 'none':
                                        filled_stars.append(svg)
                                    elif svg.find('path', {'fill': lambda x: x and x != 'none'}):
                                        filled_stars.append(svg)
                                    elif any('filled' in cls.lower() for cls in svg.get('class', [])):
                                        filled_stars.append(svg)
                                
                                if filled_stars:
                                    # If we have 1-5 filled stars, that's our rating
                                    star_count = len(filled_stars)
                                    if 1 <= star_count <= 5:
                                        rating = str(star_count)
                                    print(f"[DEBUG] Found {star_count} filled SVG stars")
                                
                                # If that doesn't work, look for text near the stars
                                if rating == "N/A":
                                    for star in svg_stars:
                                        parent = star.parent
                                        if parent:
                                            # Look for text nearby that might contain the rating
                                            text = parent.get_text(strip=True)
                                            numbers = re.findall(r'(\d+(\.\d+)?)', text)
                                            if numbers:
                                                for num in numbers:
                                                    if 1 <= float(num[0]) <= 5:
                                                        rating = num[0]
                                                        break
                                                if rating != "N/A":
                                                    break
                        except Exception as e:
                            print(f"[DEBUG] Error extracting SVG stars: {e}")
                            pass

                    # APPROACH 3: Check any text containing rating patterns
                    if rating == "N/A":
                        for element in section.find_all(text=True):
                            try:
                                text = str(element).strip()
                                # Look for patterns like "Rated 4.0" or "4.5/5" or "rating: 3"
                                rating_patterns = ['rated', '/5', 'rating', 'stars', 'star', 'voted', 'gave']
                                if any(pattern in text.lower() for pattern in rating_patterns):
                                    numbers = re.findall(r'(\d+(\.\d+)?)', text)
                                    if numbers:
                                        for num in numbers:
                                            if 1 <= float(num[0]) <= 5:
                                                rating = num[0]
                                                break
                                        if rating != "N/A":
                                            break
                            except Exception:
                                continue

                    # APPROACH 4: Look for any element with single digit 1-5
                    if rating == "N/A":
                        for element in section.find_all():
                            try:
                                text = element.get_text(strip=True)
                                if text in ['1', '2', '3', '4', '5']:
                                    # Make sure it's not part of another text like "15 comments"
                                    if len(text) == 1 or text[1] in ['.', ' '] or len(element.find_all()) == 0:
                                        rating = text[0]  # Just take the first character to be safe
                                        break
                            except Exception:
                                continue

                    # Extract rating number from the specific structure you provided
                    rating_elem = section.select_one("div.sc-lq7bklc-1.clJcgx")
                    if rating_elem:
                        rating = rating_elem.get_text(strip=True)
                        extraction_method = "div.sc-lq7bklc-1.clJcgx (HTML rating)"
                    else:
                        rating = "N/A"

                    # Extract rating type from the specific structure you provided
                    rating_type_elem = section.select_one("div.sc-lq7bklc-9.dYrjiW")
                    if rating_type_elem:
                        rating_type = rating_type_elem.get_text(strip=True)
                    
                    # Extract date from the specific structure you provided
                    date_elem = section.select_one("p.sc-lhez2tp-0.fKvqMN.time-stamp")
                    if date_elem:
                        date = date_elem.get_text(strip=True)
                    
                    # Extract review text (based on actual HTML structure)
                    text_selectors = [
                        "p.sc-1hez2tp-0.sc-hfLElm.hreYiP",  # Specific class for review text
                        "p.sc-1hez2tp-0.sc-hfLElm",
                        "p[class*='hreYiP']",
                        "section p",
                        "p[class*='review-text']",
                        "div[class*='review-text']",
                        "span[class*='review-text']",
                    ]

                    review_text = "N/A"
                    for text_sel in text_selectors:
                        text_elem = section.select_one(text_sel)
                        if (
                            text_elem and len(text_elem.get_text(strip=True)) > 10
                        ):  # Ensure it's actual review text
                            review_text = text_elem.get_text(strip=True)
                            break

                    # Extract date (based on actual HTML structure)
                    date_selectors = [
                        "p.sc-lhez2tp-0.fKvqMN.time-stamp",  # Updated specific class for timestamps based on your HTML
                        "p.sc-1hez2tp-0.fKvqMN.time-stamp",  # Previous specific class for timestamps
                        "p.sc-1hez2tp-0.fKvqMN",
                        "p[class*='time-stamp']",
                        "p[color='#9C9C9C']",
                        "span[class*='time']",
                        "div[class*='date']",
                        "time",
                    ]

                    date = "N/A"
                    for date_sel in date_selectors:
                        date_elem = section.select_one(date_sel)
                        if date_elem and date_elem.get_text(strip=True):
                            # Skip if it contains text like "Votes" or "Comments"
                            date_text = date_elem.get_text(strip=True)
                            if not any(
                                word in date_text.lower()
                                for word in ["vote", "comment", "helpful"]
                            ):
                                date = date_text
                                break
                                
                    # Keep rating as N/A if not found - we'll get it from JSON-LD later
                    if rating == "N/A":
                        extraction_method = f"{selector} (no rating found)"
                    else:
                        extraction_method = selector

                    # Only add if we have meaningful data
                    if (
                        reviewer != "N/A"
                        or rating != "N/A"
                        or (review_text != "N/A" and len(review_text) > 5)
                    ):
                        all_reviews.append(
                            {
                                "restaurant_name": restaurant_name,
                                "reviewer": reviewer,
                                "rating": rating,
                                "rating_type": rating_type,
                                "review_text": review_text,
                                "date": date,
                                "extraction_method": extraction_method,
                            }
                        )

                except Exception as e:
                    print(f"[DEBUG] Error parsing review {idx + 1}: {e}")
                    continue

            # If we found reviews, break out of the loop
            if all_reviews:
                break

    return all_reviews


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
        os.path.join(os.path.dirname(__file__), "../../data/raw/zomato_restaurants.csv")
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

# Select restaurants based on demo mode
if DEMO_MODE:
    # Demo mode: Use just 1 restaurant for testing
    restaurants_to_scrape = restaurant_df[5:6]  # Take just one restaurant (the 6th one)
    print(f"[DEBUG] DEMO MODE: Will scrape just 1 restaurant for testing")
else:
    # Actual mode: Use all restaurants
    restaurants_to_scrape = restaurant_df
    print(f"[DEBUG] ACTUAL MODE: Will scrape all {len(restaurants_to_scrape)} restaurants")

print(f"[DEBUG] Restaurants to scrape:")
for i, (idx, row) in enumerate(restaurants_to_scrape.iterrows()):
    # In actual mode, only print the first 10 and last 5 to avoid overwhelming output
    if not DEMO_MODE and i > 10 and i < len(restaurants_to_scrape) - 5:
        if i == 11:
            print(f"  ... and {len(restaurants_to_scrape) - 15} more restaurants ...")
        continue
    print(f"  {i+1}. {row['name']}")

print("\n[DEBUG] Creating stealth driver...")
driver = create_stealth_driver()

# Ensure variables are always defined
df = pd.DataFrame()
all_reviews = []
csv_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/raw/zomato_reviews.csv")
)

if not driver:
    print("[ERROR] Failed to create driver. Exiting.")
    exit(1)

try:
    # Process each restaurant
    for i, (restaurant_idx, restaurant_row) in enumerate(restaurants_to_scrape.iterrows()):
        restaurant_name = restaurant_row['name']
        restaurant_url = restaurant_row['url']
        
        print(f"\n[DEBUG] \n=== PROCESSING RESTAURANT {i+1}/5: {restaurant_name} ===")
        
        # Extract city and restaurant slug from URL
        targeted_city, restaurant_slug = extract_restaurant_info_from_url(restaurant_url)
        
        if not targeted_city or not restaurant_slug:
            print(f"[ERROR] Could not parse URL: {restaurant_url}")
            continue
            
        base_url = f"https://www.zomato.com/{targeted_city}/{restaurant_slug}"

        # First visit the main restaurant page
        print(f"[DEBUG] Visiting main restaurant page: {base_url}")
        driver.get(base_url)
        time.sleep(random.uniform(3, 6))
        bypass_app_wall(driver)

        # Now navigate to reviews
        reviews_url = f"{base_url}/reviews"
        print(f"[DEBUG] Loading reviews page: {reviews_url}")
        driver.get(reviews_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)
        bypass_app_wall(driver)

        # --- PAGINATION LOOP ---
        restaurant_reviews = []
        page_num = 1
        max_pages = 5 if DEMO_MODE else float('inf')  # In demo mode, limit pages; in actual mode, no limit
        pagination_complete = False
        
        while page_num <= max_pages and not pagination_complete:
            print(f"[DEBUG] Scraping reviews from page {page_num}...")
            
            # Wait for page to fully load
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "section"))
                )
            except TimeoutException:
                print(f"[DEBUG] Timeout waiting for page content to load")
            
            time.sleep(2)  # Additional wait for dynamic content
            
            # Try to trigger loading of more reviews by scrolling multiple times
            for scroll_attempt in range(3):
                print(f"[DEBUG] Scroll attempt {scroll_attempt + 1}/3")
                human_like_scroll(driver, pause_time=2)
                time.sleep(2)
                
                # Check if more content loaded
                current_reviews = len(driver.find_elements(By.CSS_SELECTOR, "section, div[class*='review'], div[class*='Review']"))
                time.sleep(1)
                new_reviews = len(driver.find_elements(By.CSS_SELECTOR, "section, div[class*='review'], div[class*='Review']"))
                if new_reviews == current_reviews:
                    print(f"[DEBUG] No new reviews loaded after scroll {scroll_attempt + 1}")
                else:
                    print(f"[DEBUG] New reviews detected after scroll, continuing...")
            
            # Wait a bit more after scrolling to ensure all content is loaded
            time.sleep(3)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # Primary method: HTML parsing to get all reviews from the page
            # First try HTML extraction
            page_reviews = extract_reviews_with_multiple_selectors(soup, restaurant_name)
            
            # Always extract from JSON-LD as well to get ratings
            json_reviews = extract_reviews_from_json_ld(soup)
            
            if page_reviews:
                print(f"[DEBUG] ✅ Found {len(page_reviews)} reviews via HTML extraction")
                
                # If we have both HTML and JSON-LD reviews, try to match them by reviewer name
                # to get the ratings from JSON-LD
                if json_reviews:
                    print(f"[DEBUG] Also found {len(json_reviews)} reviews in JSON-LD data")
                    # Create a dictionary of JSON-LD reviews by reviewer name for quick lookup
                    json_reviews_by_reviewer = {r['reviewer']: r for r in json_reviews}
                    
                    # Update HTML reviews with ratings from JSON-LD where possible
                    enhanced_count = 0
                    for html_review in page_reviews:
                        reviewer_name = html_review['reviewer']
                        if reviewer_name in json_reviews_by_reviewer:
                            # Get rating from JSON-LD data
                            json_review = json_reviews_by_reviewer[reviewer_name]
                            
                            # Always update rating from JSON-LD (it's more reliable)
                            html_review['rating'] = json_review['rating']
                            html_review['extraction_method'] = f"{html_review['extraction_method']} + json-ld rating"
                            enhanced_count += 1
                                
                            # Also update review text if it was missing from HTML
                            if html_review['review_text'] == "N/A" and json_review['review_text'] != "N/A":
                                html_review['review_text'] = json_review['review_text']
                    
                    # For reviews that couldn't be matched from HTML but exist in JSON-LD, add them directly
                    html_reviewer_names = {r['reviewer'] for r in page_reviews}
                    for json_review in json_reviews:
                        if json_review['reviewer'] not in html_reviewer_names:
                            # Add the JSON-LD review directly
                            json_review['restaurant_name'] = restaurant_name
                            page_reviews.append(json_review)
                            enhanced_count += 1
                    
                    if enhanced_count > 0:
                        print(f"[DEBUG] Enhanced/added {enhanced_count} reviews with data from JSON-LD")
                
                restaurant_reviews.extend(page_reviews)
                print(f"[DEBUG] Total reviews collected for {restaurant_name}: {len(restaurant_reviews)}")
            elif json_reviews:
                # Fallback to JSON-LD if HTML parsing fails
                print(f"[DEBUG] ⚠️ Found {len(json_reviews)} reviews via JSON-LD extraction (limited sample)")
                for review in json_reviews:
                    review['restaurant_name'] = restaurant_name
                restaurant_reviews.extend(json_reviews)
                print(f"[DEBUG] Total reviews collected for {restaurant_name}: {len(restaurant_reviews)}")
            else:
                    # More sophisticated blocking detection
                    blocking_indicators = [
                        "Continue in app", "Log in to continue", "Sign up now", "Download our app",
                        "Get the Zomato app", "Create your account", "Join Zomato"
                    ]
                    page_text = soup.get_text().lower()
                    strong_blocks = sum(1 for indicator in blocking_indicators if indicator.lower() in page_text)
                    
                    # Only consider blocked if multiple strong indicators or no review content at all
                    if strong_blocks >= 2 or (
                        "reviews" not in page_text and 
                        "restaurant" not in page_text and 
                        len(page_text.strip()) < 1000
                    ):
                        print("[DEBUG] ❌ Blocked by login/app wall.")
                        debug_file = os.path.join(os.path.dirname(__file__), "../../debug_blocked_page.html")
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(page_source)
                        try:
                            driver.save_screenshot(os.path.join(os.path.dirname(__file__), "../../debug_blocked_page.png"))
                        except:
                            pass
                        break
                    else:
                        print("[DEBUG] ⚠️ No reviews found on this page, but not clearly blocked. Continuing...")

            # Try to find and click the next page button
            try:
                print(f"[DEBUG] \n=== PAGE {page_num} PAGINATION DEBUG ===")
                print(f"[DEBUG] Current URL: {driver.current_url}")
                
                # Wait for pagination to be loaded
                time.sleep(2)
                
                # First try to find the next button by looking for common pagination patterns
                next_btn_selectors = [
                    "a[href*='page='][href*='sort=dd'][href*='filter=reviews-dd']:has(svg[aria-labelledby*='chevron-right'])",  # Next link with chevron icon
                    "a.sc-hWWTYC.sc-eOnLuU.sc-igaqVs.hQyaKa",  # Specific next button class from HTML
                    "a[href*='page=']:has(i[class*='chevron-right'])",  # Link with chevron-right icon
                    "div.sc-lccPpP a:last-child",  # Last pagination link
                    "a[href*='page='][href*='reviews']:not([href*='page=1'])",  # Any pagination link that's not page 1
                    "a[href*='page=']",  # Any pagination link
                ]
                
                # Also search for all pagination links to debug
                all_pagination_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='page=']")
                print(f"[DEBUG] Found {len(all_pagination_links)} pagination links total")
                for i, link in enumerate(all_pagination_links):
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"[DEBUG] Pagination link {i+1}: href='{href}', text='{text}'")
                
                next_btn = None
                next_href = None
                
                # Try different approaches to find the next page link
                for selector in next_btn_selectors:
                    try:
                        found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        print(f"[DEBUG] Selector '{selector}' found {len(found_elements)} elements")
                        
                        for element in found_elements:
                            href = element.get_attribute('href')
                            if href and 'page=' in href:
                                # Extract page number from href
                                page_match = re.search(r'page=(\d+)', href)
                                if page_match:
                                    page_num_in_href = int(page_match.group(1))
                                    print(f"[DEBUG] Found link to page {page_num_in_href}: {href}")
                                    
                                    # Look for the next page (current page + 1)
                                    if page_num_in_href == page_num + 1:
                                        next_btn = element
                                        next_href = href
                                        print(f"[DEBUG] ✅ Found next page button! Page {page_num} -> {page_num_in_href}")
                                        break
                        
                        if next_btn:
                            break
                            
                    except Exception as e:
                        print(f"[DEBUG] Error with selector '{selector}': {e}")
                        continue
                
                # If we didn't find a specific next button, try to construct the next page URL
                if not next_btn and all_pagination_links:
                    print(f"[DEBUG] No next button found via selectors, constructing next page URL...")
                    current_url = driver.current_url
                    
                    # Try to construct next page URL
                    if 'page=' in current_url:
                        # Replace existing page parameter
                        next_url = re.sub(r'page=\d+', f'page={page_num + 1}', current_url)
                    else:
                        # Add page parameter
                        separator = '&' if '?' in current_url else '?'
                        if 'sort=' in current_url:
                            next_url = current_url.replace('sort=', f'page={page_num + 1}&sort=')
                        else:
                            next_url = f"{current_url}{separator}page={page_num + 1}&sort=dd&filter=reviews-dd"
                    
                    print(f"[DEBUG] Constructed next URL: {next_url}")
                    
                    # Navigate directly
                    driver.get(next_url)
                    page_num += 1
                    time.sleep(random.uniform(3, 5))
                    
                    # Verify we're on the right page
                    new_url = driver.current_url
                    if f'page={page_num}' in new_url:
                        print(f"[DEBUG] ✅ Successfully navigated to page {page_num}")
                        continue
                    else:
                        print(f"[DEBUG] ❌ Failed to navigate to page {page_num}")
                        pagination_complete = True
                        break
                
                elif next_btn and next_href:
                    print(f"[DEBUG] Clicking next page button to: {next_href}")
                    
                    # Scroll the button into view and click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                    time.sleep(1)
                    
                    # Try to click with JavaScript if regular click fails
                    try:
                        next_btn.click()
                        print(f"[DEBUG] ✅ Clicked next button successfully")
                    except Exception as click_error:
                        print(f"[DEBUG] Regular click failed: {click_error}, trying JavaScript click")
                        driver.execute_script("arguments[0].click();", next_btn)
                        print(f"[DEBUG] ✅ JavaScript click executed")
                        
                    # Since this uses JavaScript-based pagination, URL might not change
                    # Instead, wait for new content to load and verify new reviews
                    print(f"[DEBUG] Waiting for new content to load (JavaScript pagination)...")
                    
                    # Get current review content for comparison
                    old_reviews_content = soup.get_text()
                    old_review_count = len(page_reviews)
                    
                    # Wait for content to change
                    max_wait_time = 15  # seconds
                    wait_interval = 0.5
                    content_changed = False
                    
                    for wait_attempt in range(int(max_wait_time / wait_interval)):
                        time.sleep(wait_interval)
                        current_source = driver.page_source
                        current_soup = BeautifulSoup(current_source, "html.parser")
                        current_reviews = extract_reviews_with_multiple_selectors(current_soup, restaurant_name)
                        
                        # Check if content has changed (different reviews or different content)
                        new_content = current_soup.get_text()
                        if (len(current_reviews) > 0 and 
                            (new_content != old_reviews_content or 
                             len(current_reviews) != old_review_count or
                             any(r['reviewer'] not in [old_r['reviewer'] for old_r in page_reviews] for r in current_reviews))):
                            content_changed = True
                            print(f"[DEBUG] ✅ New content detected after {(wait_attempt + 1) * wait_interval:.1f}s")
                            print(f"[DEBUG] Old review count: {old_review_count}, New review count: {len(current_reviews)}")
                            break
                    
                    if content_changed:
                        page_num += 1
                        print(f"[DEBUG] ✅ Successfully moved to page {page_num}")
                        # Continue to next iteration to scrape the new content
                    else:
                        print(f"[DEBUG] ❌ No new content loaded after {max_wait_time}s. Pagination may be complete.")
                        pagination_complete = True
                        break
                else:
                    print(f"[DEBUG] ❌ No next page button found with any method. Pagination complete.")
                    print(f"[DEBUG] Total pages scraped for {restaurant_name}: {page_num}")
                    pagination_complete = True
                    break
                    
            except Exception as e:
                print(f"[DEBUG] No next page button found or error occurred: {e}. Pagination complete.")
                pagination_complete = True
                break
        
        # Add restaurant reviews to main collection
        all_reviews.extend(restaurant_reviews)
        print(f"[DEBUG] \n=== COMPLETED {restaurant_name}: {len(restaurant_reviews)} reviews across {page_num} pages ===")
        if pagination_complete:
            print(f"[DEBUG] All available review pages were processed.")
        elif DEMO_MODE:
            print(f"[DEBUG] Stopped after {max_pages} pages due to DEMO_MODE.")
        print(f"[DEBUG] Total reviews across all restaurants: {len(all_reviews)}\n")
        
        # Delay between restaurants
        if i < len(restaurants_to_scrape) - 1:
            delay = random.uniform(5, 10)
            print(f"[DEBUG] Waiting {delay:.1f}s before next restaurant...")
            time.sleep(delay)

    # ---------------------------------------------
    # STEP 5: Save to CSV + Debug Files
    # ---------------------------------------------

    output_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/raw")
    )
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "zomato_reviews.csv")
    html_path = os.path.join(output_dir, "debug_final.html")
    screenshot_path = os.path.join(output_dir, "debug_final.png")

    # Save reviews to CSV
    if all_reviews:
        df = pd.DataFrame(all_reviews)
        df.to_csv(csv_path, index=False)
        mode_str = "DEMO" if DEMO_MODE else "ACTUAL"
        print(f"[DEBUG] ✅ {mode_str} MODE: Saved {len(all_reviews)} reviews from {len(restaurants_to_scrape)} restaurants to: {csv_path}")

        # Print sample reviews for verification
        print("\n[DEBUG] Sample reviews:")
        for i, review in enumerate(all_reviews[:3]):
            print(f"Review {i+1}:")
            for key, value in review.items():
                print(
                    f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}"
                )
            print()
    else:
        # Still create empty CSV
        empty_df = pd.DataFrame(
            columns=["restaurant_name", "reviewer", "rating", "rating_type", "review_text", "date", "extraction_method"]
        )
        empty_df.to_csv(csv_path, index=False)
        print(f"[DEBUG] ⚠️ No reviews extracted. Saved empty CSV to: {csv_path}")

    # Save debug files
    page_source = ""
    if 'page_source' in locals():
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page_source)

    try:
        driver.save_screenshot(screenshot_path)
    except Exception as e:
        print(f"[DEBUG] Could not save screenshot: {e}")

    print(f"[DEBUG] Debug files saved: {html_path}, {screenshot_path}")

except Exception as e:
    print(f"[ERROR] Script failed: {e}")
    import traceback

    traceback.print_exc()

finally:
    driver_status = "closed"
    try:
        if driver:
            driver.quit()
            print("[DEBUG] Driver closed successfully.")
    except Exception as e:
        driver_status = "close_failed"
        print(f"[DEBUG] Driver close failed: {e}")

    # Add driver status to CSV (as a new column for all rows, or as a single row if empty)
    try:
        if "df" in locals() and not df.empty:
            df["driver_status"] = driver_status
            df.to_csv(csv_path, index=False)
        elif all_reviews:
            temp_df = pd.DataFrame(all_reviews)
            temp_df["driver_status"] = driver_status
            temp_df.to_csv(csv_path, index=False)
        else:
            empty_df = pd.DataFrame(
                [
                    {
                        "restaurant_name": "",
                        "reviewer": "",
                        "rating": "",
                        "rating_type": "",
                        "review_text": "",
                        "date": "",
                        "extraction_method": "",
                        "driver_status": driver_status,
                    }
                ]
            )
            empty_df.to_csv(csv_path, index=False)
        print(f"[DEBUG] Driver status '{driver_status}' written to CSV: {csv_path}")
    except Exception as e:
        print(f"[DEBUG] Could not write driver status to CSV: {e}")
