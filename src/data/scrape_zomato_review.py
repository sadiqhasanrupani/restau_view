from selenium import webdriver  # Import webdriver from Selenium
from selenium.webdriver.chrome.service import Service  # Import Service for ChromeDriver
from selenium.webdriver.common.by import By  # Import By for locating elements
from selenium.webdriver.chrome.options import Options  # Import Options for Chrome
from selenium_stealth import stealth  # Import stealth for anti-detection

import time  # Import time for sleep functionality
import pandas as pd  # Import pandas for data manipulation
import os  # Import os for file operations

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

"""
  # Step one: Set up Chrome with selenium-stealth and anti-bot measures
  # - Configure Chrome options to run in headless mode for automation.
  # - Set a realistic User-Agent string to mimic a real browser and avoid detection.
  # - Disable automation flags and extensions that can reveal Selenium usage.
  # - Use selenium-stealth to further mask Selenium's presence by spoofing browser properties.
  # - Initialize the ChromeDriver with these options.
"""

# Set up Chrome with selenium-stealth to avoid detection
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Browser in headless mode
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)  # Set a common User-Agent

# Disable automation flags to avoid detection
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# Set path to ChromeDriver
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

# Create the Browser driver
service = Service(CHROMEDRIVER_PATH)  # Create a Service object for ChromeDriver
driver = webdriver.Chrome(
    service=service, options=chrome_options
)  # Initialize ChromeDriver with options

# Add stealth to the driver to mask Selenium automation
stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

# Open Zomato search page for a Pune location
# Targeted city
targeted_city = "pune"
restaurant_slug = "2bhk-diner-key-club-bund-garden"
URL = f"https://www.zomato.com/{targeted_city}/{restaurant_slug}/reviews"  # URL for Zomato Pune page
driver.get(URL)  # Navigate to Zomato Pune page

# Wait for a key element to be present instead of using time.sleep
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

"""
  # Step three: Scroll to load more restaurants
  # - Scroll down the page multiple times to trigger dynamic loading of more restaurant cards.
  # - Use time.sleep between scrolls to allow new content to load.
  # - Adjust the number of scrolls as needed for more or fewer results.
"""
for _ in range(5):  # Adjust the range for more or fewer scrolls
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )  # Scroll to the bottom of the page
    time.sleep(10)  # Wait for new content to load


# --- Scrape reviews from each restaurant's /reviews page ---
all_reviews = []

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
os.makedirs(output_dir, exist_ok=True)
reviews_output_path = os.path.join(output_dir, "zomato_reviews.csv")

reviews_df = pd.DataFrame(all_reviews)

# Save reviews to CSV
reviews_df.to_csv(reviews_output_path, index=False)

print(reviews_df.head())

# for rest in restaurant_data[:1]:  # Limit for demo; remove slice for all
#     rest_url = rest["url"]
#     if rest_url == "N/A":
#         continue
#     # Build reviews URL if not already
#     if rest_url.endswith("/reviews"):
#         reviews_url = rest_url
#     else:
#         reviews_url = rest_url.rstrip("/") + "/reviews"
#     page = 1
#     while True:
#         paged_url = f"{reviews_url}?page={page}&sort=dd&filter=reviews"
#         print(f"\n[DEBUG] Loading page: {paged_url}")
#         driver.get(paged_url)
#         import time
#         time.sleep(3)  # Give JS time to load

#         # Try to close modal/pop-up if present
#         try:
#             print("[DEBUG] Attempting to close modals/pop-ups...")
#             for selector in [
#                 "i.sc-rbbb40-1.eDwwcN",  # your current selector
#                 "i.sc-rbbb40-1.iFnyeo",  # another common one
#                 ".sc-re4bd0-1.btYpry",   # modal close
#                 ".sc-1yb42gd-0.eqIZjw + i"  # close icon next to empty span
#             ]:
#                 try:
#                     close_btn = driver.find_element(By.CSS_SELECTOR, selector)
#                     print(f"[DEBUG] Found and clicking modal close button: {selector}")
#                     close_btn.click()
#                     time.sleep(1)
#                 except Exception as e:
#                     # Uncomment for verbose debugging:
#                     # print(f"[DEBUG] No modal for selector {selector}: {e}")
#                     continue
#         except Exception as e:
#             print(f"[DEBUG] Exception in modal closing: {e}")

#         # After loading the page and closing modals
#         page_source = driver.page_source

#         # Early check for login/app wall
#         if "Continue in app" in page_source or "Log in" in page_source:
#             print("[DEBUG] Detected login/app wall before waiting for reviews.")
#             # Always save screenshot for debug
#             driver.save_screenshot(f"debug_blocked_page_{page}.png")
#             print(f"[DEBUG] Saved screenshot for blocked page {page}")
#             # Save page source for manual inspection
#             with open(f"debug_blocked_page_{page}.html", "w", encoding="utf-8") as f:
#                 f.write(page_source)
#             break

#         # Use BeautifulSoup to parse reviews if present
#         soup = BeautifulSoup(page_source, "html.parser")
#         review_sections = soup.select("section.sc-1q7bklc-0.bpzXW2")
#         print(f"[DEBUG][BS4] Found {len(review_sections)} review sections with BeautifulSoup on page {page}")
#         if not review_sections:
#             print("[DEBUG][BS4] No review sections found, breaking loop.")
#             # Always save screenshot for debug
#             driver.save_screenshot(f"debug_no_reviews_{page}.png")
#             print(f"[DEBUG] Saved screenshot for no reviews page {page}")
#             # Save page source for manual inspection
#             with open(f"debug_no_reviews_{page}.html", "w", encoding="utf-8") as f:
#                 f.write(driver.page_source)
#             print("[DEBUG] Blocked by login/app wall or reviews not found.")
#             break

#         for idx, section in enumerate(review_sections):
#             try:
#                 print(f"[DEBUG][BS4] Parsing review section {idx+1}/{len(review_sections)}")
#                 reviewer = section.select_one("p.sc-1hez2tp-0") or \
#                            section.select_one("p.sc-1hez2tp-0")
#                 reviewer = reviewer.get_text(strip=True) if reviewer else "N/A"
#                 rating = section.select_one("div.sc-1hez2tp-2.bc-iwdsyN.bjBOe") or \
#                          section.select_one("span[style*='background-color']")
#                 rating = rating.get_text(strip=True) if rating else "N/A"
#                 review_text = section.select_one("p.sc-1hez2tp-0")
#                 review_text = review_text.get_text(strip=True) if review_text else "N/A"
#                 date = section.select_one("div.sc-1hez2tp-0")
#                 date = date.get_text(strip=True) if date else "N/A"
#                 review_type = section.select_one("span.sc-lewbjd.gpZKqA")
#                 review_type = review_type.get_text(strip=True) if review_type else "N/A"
#                 location = rest.get("area", "N/A")

#                 all_reviews.append({
#                     "restaurant": rest["name"],
#                     "location": location,
#                     "rating": rating,
#                     "review_type": review_type,
#                     "review_text": review_text,
#                     "reviewer": reviewer,
#                     "date": date,
#                     "restaurant_url": rest_url
#                 })
#             except Exception as e:
#                 print(f"⚠️ [BS4] Error parsing review: {e}")
#                 continue

#         # Check if there is a next page (pagination)
#         try:
#             print("[DEBUG] Checking for next page button...")
#             next_btn = driver.find_element(By.CSS_SELECTOR, "a.sc-1w7j1y1-1.dQQUmK")
#             next_btn_class = next_btn.get_attribute("class")
#             print(f"[DEBUG] Next button class: {next_btn_class}")
#             if next_btn_class is not None and "disabled" in next_btn_class:
#                 print("[DEBUG] Next button is disabled, breaking.")
#                 break
#             else:
#                 print("[DEBUG] Going to next page.")
#                 page += 1
#         except Exception as e:
#             print(f"[DEBUG] No next page button found: {e}")
#             break
