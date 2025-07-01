import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
from src.utils.helpers import get_random_headers, random_sleep, fetch_page, save_content, extract_zomato_pagination, save_html_pages_dynamic

# Enable debug mode for verbose logging
DEBUG = True
from src.utils.helpers import create_logger

# Log file path
log_file = "src/logger/extract_zomator_htmls.log"
# Create a logger instance
logger = create_logger(__name__, log_file, level=(10 if DEBUG else 20))

def main():
    """
    This script fetches and saves the HTML content of a Zomato restaurant's review page.
    Functions:
    ----------
    main():
        Main entry point for the script. 
        - Constructs the URL for a specific restaurant's review page on Zomato.
        - Initiates an HTTP session and fetches the page content using `fetch_page`.
        - If the response is valid, logs and prints debug information about the HTTP response.
        - Checks if the fetched content appears to be valid HTML and logs the result.
        - Saves the HTML content to a local file for further analysis.
    Dependencies:
    -------------
    - requests: For HTTP requests and session management.
    - logger: For logging debug and info messages.
    - fetch_page: Custom function to fetch a web page using a session.
    - save_content: Custom function to save text content to a file.
    Constants:
    ----------
    - DEBUG: Boolean flag to enable or disable debug output.
    Usage:
    ------
    Run this script to download and locally store the HTML of a Zomato restaurant's review page for further data analysis or processing.
    """
    # Set city and restaurant slug
    city = "Pune"
    restaurant = "foo-kopa-mundhwa"
    # Construct the Zomato review page URL
    url = f"https://www.zomato.com/{city}/{restaurant}/reviews"
    # Start a new HTTP session
    session = requests.Session()
    # Fetch the page using a custom helper
    resp = fetch_page(url, session)
    if not resp:
        # Exit if no response
        return

    if DEBUG:
        # Log and print HTTP response details
        logger.debug(f"Status code: {resp.status_code}")
        logger.debug(f"Content-Type: {resp.headers.get('content-type', 'Unknown')}")
        logger.debug(
            f"Content-Encoding: {resp.headers.get('content-encoding', 'None')}"
        )
        logger.debug(f"Response length: {len(resp.text)} characters")
        print(f"[DEBUG] Status code: {resp.status_code}")
        print(f"[DEBUG] Content-Type: {resp.headers.get('content-type', 'Unknown')}")
        print(
            f"[DEBUG] Content-Encoding: {resp.headers.get('content-encoding', 'None')}"
        )
        print(f"[DEBUG] Response length: {len(resp.text)} characters")

    # Check if we got valid HTML
    if resp.text.strip().startswith("<!DOCTYPE") or resp.text.strip().startswith(
        "<html"
    ):
        # Log and print valid HTML content
        logger.info("✓ Received valid HTML content")
        logger.debug(f"First 200 characters: {resp.text[:200]}")
        print("✓ Received valid HTML content")
        print(f"First 200 characters: {resp.text[:200]}")
    else:
        # Log and print invalid HTML warning
        logger.warning("✗ Response doesn't appear to be valid HTML")
        logger.debug(f"First 200 characters: {repr(resp.text[:200])}")
        print("✗ Response doesn't appear to be valid HTML")
        print(f"First 200 characters: {repr(resp.text[:200])}")

    # Save the HTML content to a local file
    is_content_saved, err = save_content(resp.text, "./data/raw/zomato_review_page.html")
    if err:
        logger.error(f"Failed to save content: {err}")
        print(f"[ERROR] Failed to save content: {err}")
        return
    
    if is_content_saved:
        logger.info("✓ Content saved successfully")
        print("✓ Content saved successfully")

        # using beautifulsoup to parse the HTML
        soup = BeautifulSoup(resp.text, 'html.parser')

        # getting the title of the page
        title = soup.title.string if soup.title else "No title found"
        print(f"Page title: {title}")
        logger.debug(f"Page title: {title}")

        # Extract pagination information using reusable function
        base_url = "https://www.zomato.com"
        pagination_info = extract_zomato_pagination(resp.text, base_url)
        
        # Extract specific values for backward compatibility
        pagination_hrefs = pagination_info['pagination_hrefs']
        has_next = pagination_info['has_next']
        current_page = pagination_info['current_page']
        total_pages = pagination_info['total_pages']
        page_links = pagination_info['page_links']

        # Log and print pagination information
        logger.debug(f"Pagination hrefs: {pagination_hrefs}")
        logger.debug(f"Has next page: {has_next}")
        logger.debug(f"Current page: {current_page}")
        logger.debug(f"Total pages: {total_pages}")
        logger.debug(f"Page links: {page_links}")
        
        print(f"Pagination hrefs: {pagination_hrefs}")
        print(f"Has next page: {has_next}")
        if current_page:
            print(f"Current page: {current_page}")
        if total_pages:
            print(f"Total pages: {total_pages}")
        if page_links:
            print(f"Available pages: {[link['page_number'] for link in page_links]}")
        
        # Use dynamic pagination to discover and save ALL pages
        print(f"\n🔄 Using dynamic pagination discovery to find and save ALL pages...")
        logger.info("Starting dynamic pagination discovery")
        
        # Use dynamic pagination function
        dynamic_results = save_html_pages_dynamic(
            base_url=base_url,
            initial_url=url,
            restaurant=restaurant,
            session=session,
            max_pages=None  # No limit - get all pages
        )
        
        # Report results
        print(f"\n🎉 Dynamic pagination discovery completed!")
        print(f"📄 Total pages discovered: {dynamic_results['total_pages_found']}")
        print(f"💾 Pages successfully saved: {dynamic_results['pages_saved']}")
        print(f"📁 Directory: data/raw/html/zomato/restaurants/{restaurant}/review_pages/")
        
        if dynamic_results['errors']:
            print(f"⚠️ Errors encountered: {len(dynamic_results['errors'])}")
            for error in dynamic_results['errors']:
                print(f"   - {error}")
        
        logger.info(f"Dynamic pagination completed: {dynamic_results['pages_saved']} pages saved")




if __name__ == "__main__":
    try:
        # Run the main function and handle any unhandled exceptions
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"[CRITICAL] Unhandled exception: {e}")
