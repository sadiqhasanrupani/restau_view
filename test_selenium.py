from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_selenium_chrome():
    """Test if Selenium works with ChromeDriver"""
    
    # Chrome options for headless browsing (optional)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # ChromeDriver service
    service = Service('/usr/bin/chromedriver')
    
    try:
        # Create webdriver instance
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test navigation
        driver.get("https://www.google.com")
        
        # Get page title
        title = driver.title
        print(f"✅ Success! Page title: {title}")
        
        # Close driver
        driver.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Selenium with ChromeDriver...")
    test_selenium_chrome()

