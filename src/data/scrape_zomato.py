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

# Get ChromeDriver path from environment variable
CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH')
if not CHROMEDRIVER_PATH:
    print("Error: CHROMEDRIVER_PATH environment variable not set.")
    print("Please set CHROMEDRIVER_PATH to the location of your chromedriver.exe")
    print("Example: $env:CHROMEDRIVER_PATH = 'C:\\path\\to\\chromedriver.exe'")
    exit(1)

# Create the Browser driver
try:
    service = Service(CHROMEDRIVER_PATH)  # Create a Service object for ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)  # Initialize ChromeDriver with options
except Exception as e:
    print(f"Error creating Chrome driver: {e}")
    print(f"ChromeDriver path: {CHROMEDRIVER_PATH}")
    print("Please ensure the ChromeDriver path is correct and the file exists.")
    exit(1)

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

"""
  # Step two: Open Zomato search page for the targeted city
  # - Build the URL for the desired city (e.g., Pune).
  # - Navigate to the Zomato restaurant listing page for that city.
  # - Wait for the page's <body> element to be present using WebDriverWait (instead of time.sleep).
"""

# Open Zomato search page for a Pune location
# Targeted city
targeted_city = "pune"
URL = f"https://www.zomato.com/{targeted_city}/restaurants"  # URL for Zomato Pune page
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

"""
  # Step four: Scrape restaurant cards from the main page
  # - Print a portion of the page source for debugging and selector verification.
  # - Attempt to locate restaurant cards using a class name or other selectors.
  # - Print the number of restaurant cards found for verification.
  # - If the selector changes, inspect the HTML and update the selector accordingly.
"""
# Debug: print a portion of the page source to help identify the correct selector
# print(driver.page_source[:500])  # Print the first 500 characters

# Use the exact class name for restaurant card wrapper
restaurant_cards = driver.find_elements(By.CSS_SELECTOR, "div.sc-evWYkj.cRThYq")
print(f"Found {len(restaurant_cards)} restaurant cards on the page.")

"""
  # Step five: Add first 5 restaurants for demo and others in a list
  # - Extract the names and other details of the first 5 restaurants.
  # - Store the details in a list or DataFrame for further processing.
  # - Print the details of the first 5 restaurants for verification.
  # - If the selector changes, inspect the HTML and update the selector accordingly. 
"""
# Extract details of the first 5 restaurants
restaurant_data = []

for card in restaurant_cards:
    try:
        # Get URL from 2nd <a>
        try:
            anchors = card.find_elements(By.TAG_NAME, "a")
            partial_url = anchors[1].get_attribute("href") if len(anchors) > 1 else None
            if partial_url:
                if partial_url.startswith("http"):
                    restaurant_url = partial_url
                elif partial_url.startswith("/"):
                    restaurant_url = f"https://www.zomato.com{partial_url}"
                else:
                    restaurant_url = partial_url
            else:
                restaurant_url = "N/A"
        except:
            restaurant_url = "N/A"

        # Get name
        try:
            name = card.find_element(By.TAG_NAME, "h4").text.strip()
        except:
            name = "N/A"

        # Get cuisine and price
        try:
            p_tags = card.find_elements(By.TAG_NAME, "p")
            cuisine = p_tags[0].text.strip() if len(p_tags) > 0 else "N/A"
            price = p_tags[1].text.strip() if len(p_tags) > 1 else "N/A"
        except:
            cuisine = "N/A"
            price = "N/A"

        # Get area
        try:
            area = card.find_element(By.CLASS_NAME, "min-basic-info-left").text.strip()
        except:
            area = "N/A"

        # Get distance
        try:
            distance = card.find_element(
                By.CLASS_NAME, "min-basic-info-right"
            ).text.strip()
        except:
            distance = "N/A"

        restaurant_data.append(
            {
                "name": name,
                "url": restaurant_url,
                "cuisine": cuisine,
                "price_for_two": price,
                "area": area,
                "distance": distance,
            }
        )

    except Exception as e:
        print(f"⚠️ Error parsing card: {e}")
        continue

# Convert to DataFrame for easier manipulation
df_restaurants = pd.DataFrame(restaurant_data)

# Ensure output directory exists before saving CSV
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "zomato_restaurants.csv")

df_restaurants.to_csv(output_path, index=False)

# Print the first 5 restaurants for verification
print(df_restaurants.head())
