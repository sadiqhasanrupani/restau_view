import random
import time
import os
from fake_useragent import UserAgent
import requests
import logging
from bs4 import BeautifulSoup

DEBUG = True

def create_logger(name: str, log_file: str, level=logging.INFO, fmt=None):
    """
    Create and return a logger with the specified name, log file, and level.
    """
    logger_dir = os.path.dirname(log_file)
    os.makedirs(logger_dir, exist_ok=True)
    if fmt is None:
        fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format=fmt,
        level=level
    )
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

logger = create_logger(__name__, "./logger/extract_zomator_htmls.log", logging.DEBUG if DEBUG else logging.INFO)

def get_random_headers():
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
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
        return True, None
    except Exception as e:
        logger.error(f"Failed to save content: {e}")
        print(f"[ERROR] Failed to save content: {e}")
        return False, e


def save_html_pages_dynamic(base_url, initial_url, restaurant, session, max_pages=None):
    """
    Save multiple HTML pages with dynamic pagination discovery.
    
    This function starts with the initial URL and progressively discovers new pagination
    links from each page until no new pages are found.

    Args:
        base_url (str): Base URL to resolve relative links.
        initial_url (str): Starting URL (usually page 1).
        restaurant (str): Restaurant identifier.
        session (requests.Session): HTTP session for fetching pages.
        max_pages (int, optional): Maximum number of pages to fetch.
        
    Returns:
        dict: Results containing saved pages info
    """
    results = {
        'pages_saved': 0,
        'total_pages_found': 0,
        'saved_files': [],
        'errors': [],
        'all_pagination_urls': set()
    }
    
    try:
        # Base directory for saving HTML files
        base_dir = os.path.join('data', 'raw', 'html', 'zomato', 'restaurants', restaurant, 'review_pages')
        os.makedirs(base_dir, exist_ok=True)

        # Track visited URLs and discovered URLs
        visited_urls = set()
        urls_to_process = [initial_url]
        page_counter = 1
        
        logger.info(f"Starting dynamic pagination discovery from: {initial_url}")
        print(f"🔍 Starting dynamic pagination discovery...")
        
        while urls_to_process and (not max_pages or page_counter <= max_pages):
            current_url = urls_to_process.pop(0)
            
            # Skip if already visited
            if current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            
            # Fetch current page
            print(f"📄 Processing page {page_counter}: {current_url}")
            resp = fetch_page(current_url, session)
            
            if not resp or resp.status_code != 200:
                error_msg = f"Failed to fetch page {page_counter}: {current_url}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                continue
            
            # Save current page
            file_name = f"page_{page_counter}.html"
            file_path = os.path.join(base_dir, file_name)
            
            is_saved, err = save_content(resp.text, file_path)
            if is_saved:
                results['pages_saved'] += 1
                results['saved_files'].append(file_path)
                print(f"✅ Saved page {page_counter}: {file_path}")
                logger.info(f"Successfully saved page {page_counter}")
            else:
                error_msg = f"Failed to save page {page_counter}: {err}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                continue
            
            # Extract pagination from current page to find new pages
            current_pagination = extract_zomato_pagination(resp.text, base_url)
            current_page_urls = set(current_pagination['pagination_hrefs'])
            results['all_pagination_urls'].update(current_page_urls)
            
            # Find new URLs that haven't been visited or queued
            new_urls = current_page_urls - visited_urls - set(urls_to_process)
            
            if new_urls:
                # Sort URLs to process them in order (if possible)
                sorted_new_urls = sorted(list(new_urls))
                urls_to_process.extend(sorted_new_urls)
                print(f"🔗 Found {len(new_urls)} new pagination links from page {page_counter}")
                logger.info(f"Discovered {len(new_urls)} new URLs from page {page_counter}: {sorted_new_urls}")
            else:
                print(f"🏁 No new pagination links found on page {page_counter}")
                logger.info(f"No new URLs found on page {page_counter}")
            
            page_counter += 1
            
            # Show progress
            print(f"📊 Progress: {len(visited_urls)} pages processed, {len(urls_to_process)} remaining")
        
        results['total_pages_found'] = len(results['all_pagination_urls'])
        
        print(f"\n🎉 Dynamic pagination discovery completed!")
        print(f"📄 Total pages discovered: {results['total_pages_found']}")
        print(f"💾 Pages successfully saved: {results['pages_saved']}")
        
        if results['errors']:
            print(f"⚠️ Errors encountered: {len(results['errors'])}")
            
        logger.info(f"Dynamic pagination completed: {results['pages_saved']} pages saved, {results['total_pages_found']} total discovered")
        
    except Exception as e:
        error_msg = f"Failed in dynamic pagination discovery: {e}"
        results['errors'].append(error_msg)
        logger.error(error_msg)
        print(f"💥 {error_msg}")
    
    return results


def save_html_pages(base_url, city, restaurant, pagination_info, session):
    """
    Save multiple HTML pages for a restaurant's review using pagination information.
    
    DEPRECATED: Use save_html_pages_dynamic() for better pagination discovery.

    Args:
        base_url (str): Base URL to resolve relative links.
        city (str): City identifier for the restaurant location.
        restaurant (str): Restaurant identifier.
        pagination_info (dict): Pagination information containing page links.
        session (requests.Session): HTTP session for fetching pages.
    """
    try:
        # Base directory for saving HTML files
        base_dir = os.path.join('data', 'raw', 'html', 'zomato', 'restaurants', restaurant, 'review_pages')

        # Ensure the directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Initialize page counter
        page_counter = 1

        # Fetch and save each page using pagination hrefs
        for page_url in pagination_info['pagination_hrefs']:
            resp = fetch_page(page_url, session)
            if resp and resp.status_code == 200:
                # Define file path
                file_name = f"page_{page_counter}.html"
                file_path = os.path.join(base_dir, file_name)

                # Save content
                is_content_saved, err = save_content(resp.text, file_path)
                if err:
                    logger.error(f"Error saving page {page_counter}: {err}")
                else:
                    logger.info(f"Page {page_counter} saved successfully")

                # Increment page counter
                page_counter += 1

            else:
                logger.error(f"Failed to fetch page {page_counter} from {page_url}")

    except Exception as e:
        logger.error(f"Failed to save HTML pages: {e}")


def extract_zomato_pagination(html_content, base_url=None):
    """
    Extract pagination information from Zomato review pages.
    
    Args:
        html_content (str): HTML content of the page
        base_url (str, optional): Base URL to resolve relative links
    
    Returns:
        dict: Dictionary containing pagination information with keys:
            - 'pagination_hrefs': List of pagination URLs
            - 'has_next': Boolean indicating if there's a next page
            - 'current_page': Current page number (if available)
            - 'total_pages': Total number of pages (if available)
            - 'page_links': List of individual page links
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize result dictionary
        result = {
            'pagination_hrefs': [],
            'has_next': False,
            'current_page': None,
            'total_pages': None,
            'page_links': []
        }
        
        # Method 1: Look for pagination container with specific class
        pagination_container = soup.find('div', class_='sc-ZxTAX')
        if not pagination_container:
            # Fallback: try alternative container classes
            pagination_container = soup.find('div', class_='sc-cHRTLU')
        
        if pagination_container:
            # Find all pagination links within the container
            pagination_links = pagination_container.find_all('a', class_=['sc-eUqAvv', 'sc-CHaGD'])
            
            if not pagination_links:
                # Try alternative link classes
                pagination_links = pagination_container.find_all('a', href=lambda href: href and ('page=' in href or 'reviews' in href))
            
            # Extract hrefs and analyze links
            for link in pagination_links:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute if base_url provided
                    if base_url and href.startswith('/'):
                        href = base_url.rstrip('/') + href
                    
                    result['pagination_hrefs'].append(href)
                    
                    # Check if this is a page number link
                    link_text = link.get_text(strip=True)
                    if link_text.isdigit():
                        result['page_links'].append({
                            'page_number': int(link_text),
                            'url': href,
                            'is_current': 'selected' in link.get('class', []) or 'active' in link.get('class', [])
                        })
                        
                        # Determine current page
                        if 'selected' in link.get('class', []) or 'active' in link.get('class', []):
                            result['current_page'] = int(link_text)
            
            # Check for next button (chevron-right icon or "Next" text)
            next_button = pagination_container.find('a', class_=['sc-lbihag', 'sc-bjbPDc', 'sc-fHmkVi'])
            if next_button:
                # Look for chevron-right icon or next indicators
                chevron_icon = next_button.find('svg')
                if (chevron_icon and 'chevron-right' in str(chevron_icon)) or 'next' in next_button.get_text().lower():
                    result['has_next'] = True
                    next_href = next_button.get('href')
                    if next_href and next_href not in result['pagination_hrefs']:
                        if base_url and next_href.startswith('/'):
                            next_href = base_url.rstrip('/') + next_href
                        result['pagination_hrefs'].append(next_href)
        
        # Method 2: Fallback - search for any links with page parameters
        if not result['pagination_hrefs']:
            page_links = soup.find_all('a', href=lambda href: href and 'page=' in href)
            for link in page_links:
                href = link.get('href')
                if href:
                    if base_url and href.startswith('/'):
                        href = base_url.rstrip('/') + href
                    result['pagination_hrefs'].append(href)
        
        # Determine total pages from page links
        if result['page_links']:
            result['total_pages'] = max(link['page_number'] for link in result['page_links'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_hrefs = []
        for href in result['pagination_hrefs']:
            if href not in seen:
                seen.add(href)
                unique_hrefs.append(href)
        result['pagination_hrefs'] = unique_hrefs
        
        # Log results if DEBUG is enabled
        if DEBUG:
            logger.debug(f"Pagination extraction results: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting pagination: {e}")
        if DEBUG:
            print(f"[ERROR] Error extracting pagination: {e}")
        return {
            'pagination_hrefs': [],
            'has_next': False,
            'current_page': None,
            'total_pages': None,
            'page_links': [],
            'error': str(e)
        }


def extract_pagination_info(soup_or_html, base_url=None):
    """
    Simplified wrapper for pagination extraction that accepts either BeautifulSoup object or HTML string.
    
    Args:
        soup_or_html: Either a BeautifulSoup object or HTML string
        base_url (str, optional): Base URL to resolve relative links
    
    Returns:
        dict: Pagination information
    """
    if isinstance(soup_or_html, BeautifulSoup):
        html_content = str(soup_or_html)
    else:
        html_content = soup_or_html
    
    return extract_zomato_pagination(html_content, base_url)
