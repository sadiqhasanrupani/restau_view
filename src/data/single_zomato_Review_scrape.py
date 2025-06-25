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
import json
from urllib.parse import urljoin


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
                        reviews.append({
                            'reviewer': review_data.get('author', 'N/A'),
                            'rating': str(review_data.get('reviewRating', {}).get('ratingValue', 'N/A')),
                            'review_text': review_data.get('description', 'N/A'),
                            'date': 'N/A',  # Not available in structured data
                            'extraction_method': 'json-ld'
                        })
                    break  # Found reviews, no need to check other scripts
            except (json.JSONDecodeError, KeyError) as e:
                continue
                
    except Exception as e:
        print(f"[DEBUG] Error extracting from JSON-LD: {e}")
        
    return reviews


def extract_reviews_with_multiple_selectors(soup):
    """Try multiple CSS selectors to find reviews"""
    all_reviews = []

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

                    # Extract rating (based on actual HTML structure)
                    rating_selectors = [
                        "div.sc-1q7bklc-1.cILgox",  # Specific class for rating numbers
                        "div.sc-1q7bklc-1",
                        "div.sc-1q7bklc-5 div.sc-1q7bklc-1",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "span[class*='star']",
                    ]

                    rating = "N/A"
                    for rat_sel in rating_selectors:
                        rat_elem = section.select_one(rat_sel)
                        if rat_elem and rat_elem.get_text(strip=True):
                            rating = rat_elem.get_text(strip=True)
                            break

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
                        "p.sc-1hez2tp-0.fKvqMN.time-stamp",  # Specific class for timestamps
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

                    # Only add if we have meaningful data
                    if (
                        reviewer != "N/A"
                        or rating != "N/A"
                        or (review_text != "N/A" and len(review_text) > 5)
                    ):
                        all_reviews.append(
                            {
                                "reviewer": reviewer,
                                "rating": rating,
                                "review_text": review_text,
                                "date": date,
                                "extraction_method": selector,
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
# MAIN SCRAPING LOGIC
# ---------------------------------------------

print("[DEBUG] Creating stealth driver...")
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
    # Target URL
    targeted_city = "pune"
    restaurant_slug = "2bhk-diner-key-club-bund-garden"
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
    all_reviews = []
    page_num = 1
    max_pages = 50  # Safety limit to prevent infinite loops
    
    while page_num <= max_pages:
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
        page_reviews = extract_reviews_with_multiple_selectors(soup)
        if page_reviews:
            print(f"[DEBUG] ✅ Found {len(page_reviews)} reviews via HTML extraction")
            all_reviews.extend(page_reviews)
            print(f"[DEBUG] Total reviews collected so far: {len(all_reviews)}")
        else:
            # Fallback to JSON-LD if HTML parsing fails (but JSON-LD only has limited reviews)
            json_reviews = extract_reviews_from_json_ld(soup)
            if json_reviews:
                print(f"[DEBUG] ⚠️ Found {len(json_reviews)} reviews via JSON-LD extraction (limited sample)")
                all_reviews.extend(json_reviews)
                print(f"[DEBUG] Total reviews collected so far: {len(all_reviews)}")
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

        # This logic is now handled above in the blocking detection section

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
                    current_reviews = extract_reviews_with_multiple_selectors(current_soup)
                    
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
                    break
            else:
                print("[DEBUG] ❌ No next page button found with any method. Pagination complete.")
                print(f"[DEBUG] Total pages scraped: {page_num}")
                break
                
        except (NoSuchElementException, Exception) as e:
            print(f"[DEBUG] No next page button found or error occurred: {e}. Pagination complete.")
            break

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
        print(f"[DEBUG] ✅ Saved {len(all_reviews)} reviews to: {csv_path}")

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
            columns=["reviewer", "rating", "review_text", "date", "extraction_method"]
        )
        empty_df.to_csv(csv_path, index=False)
        print(f"[DEBUG] ⚠️ No reviews extracted. Saved empty CSV to: {csv_path}")

    # Save debug files
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
                        "reviewer": "",
                        "rating": "",
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
