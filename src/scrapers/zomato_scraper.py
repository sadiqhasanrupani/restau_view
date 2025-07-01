"""
Zomato Scraper Module
====================

This module provides comprehensive functions for scraping Zomato restaurant data
including reviews, pagination handling, and organized file storage.

Directory Structure Created:
data/
└── raw/
    └── html/
        └── zomato/
            └── restaurants/
                └── {restaurant_name}/
                    └── review_pages/
                        ├── page_1.html
                        ├── page_2.html
                        └── ...

Functions:
    - scrape_restaurant_reviews: Main function to scrape all review pages
    - get_restaurant_info: Extract restaurant metadata
    - save_organized_files: Save files in organized structure
    - get_all_pages: Handle pagination and get all pages
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.helpers import (
    get_random_headers, 
    random_sleep, 
    fetch_page, 
    save_content, 
    extract_zomato_pagination,
    save_html_pages_dynamic,
    create_logger
)

# Create logger
logger = create_logger(__name__, "./src/logger/zomato_scraper.log")


def clean_filename(name):
    """
    Clean a string to be used as a filename or directory name.
    
    Args:
        name (str): The string to clean
        
    Returns:
        str: Cleaned string suitable for filesystem use
    """
    # Remove special characters and replace spaces with hyphens
    cleaned = re.sub(r'[^\w\s-]', '', name)
    cleaned = re.sub(r'[-\s]+', '-', cleaned)
    return cleaned.strip('-').lower()


def get_restaurant_info(soup):
    """
    Extract restaurant information from the HTML soup.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content
        
    Returns:
        dict: Restaurant information
    """
    info = {
        'name': None,
        'location': None,
        'cuisine': None,
        'rating': None,
        'city': None
    }
    
    try:
        # Extract restaurant name
        name_element = soup.find('h1', class_=lambda x: x and 'sc-' in x)
        if name_element:
            info['name'] = name_element.get_text(strip=True)
        
        # Extract location/address
        address_elements = soup.find_all(text=re.compile(r'\b(Road|Street|Lane|Avenue|Nagar|Colony)\b', re.I))
        if address_elements:
            info['location'] = address_elements[0].strip()
        
        # Extract cuisine type
        cuisine_links = soup.find_all('a', href=lambda x: x and 'restaurants' in x and any(cuisine in x.lower() for cuisine in ['asian', 'chinese', 'indian', 'italian']))
        if cuisine_links:
            cuisines = [link.get_text(strip=True) for link in cuisine_links[:3]]
            info['cuisine'] = ', '.join(cuisines)
        
        # Extract rating
        rating_element = soup.find(text=re.compile(r'^\d+\.\d+$'))
        if rating_element:
            info['rating'] = rating_element.strip()
            
    except Exception as e:
        logger.warning(f"Error extracting restaurant info: {e}")
    
    return info


def save_organized_files(content, base_dir, restaurant, page_num):
    """
    Save HTML content in an organized directory structure.
    
    Args:
        content (str): HTML content to save
        base_dir (str): Base directory for saving files
        restaurant (str): Restaurant identifier
        page_num (int): Page number
        
    Returns:
        tuple: (success, file_path, error)
    """
    try:
        # Create organized directory structure
        review_pages_dir = os.path.join(base_dir, 'zomato', 'restaurants', restaurant, 'review_pages')
        os.makedirs(review_pages_dir, exist_ok=True)
        
        # Create filename
        filename = f"page_{page_num}.html"
        file_path = os.path.join(review_pages_dir, filename)
        
        # Save content
        success, error = save_content(content, file_path)
        return success, file_path, error
        
    except Exception as e:
        logger.error(f"Error saving organized files: {e}")
        return False, None, e


def get_all_pages(base_url, initial_pagination_info, session, max_pages=None):
    """
    Get all pages using pagination information.
    
    Args:
        base_url (str): Base URL for the site
        initial_pagination_info (dict): Initial pagination information
        session (requests.Session): HTTP session
        max_pages (int, optional): Maximum number of pages to fetch
        
    Returns:
        list: List of tuples (page_num, html_content, url)
    """
    pages = []
    page_urls = initial_pagination_info['pagination_hrefs']
    
    if max_pages:
        page_urls = page_urls[:max_pages]
    
    for i, url in enumerate(page_urls, 1):
        try:
            resp = fetch_page(url, session)
            if resp and resp.status_code == 200:
                pages.append((i, resp.text, url))
                logger.info(f"Successfully fetched page {i}: {url}")
            else:
                logger.error(f"Failed to fetch page {i}: {url}")
                
        except Exception as e:
            logger.error(f"Error fetching page {i}: {e}")
            continue
    
    return pages


def scrape_restaurant_reviews(city, restaurant_slug, base_dir="data/raw/html", max_pages=None):
    """
    Main function to scrape all review pages for a Zomato restaurant.
    
    Args:
        city (str): City name (e.g., "Pune", "Mumbai")
        restaurant_slug (str): Restaurant URL slug (e.g., "foo-kopa-mundhwa")
        base_dir (str): Base directory for saving files
        max_pages (int, optional): Maximum number of pages to scrape
        
    Returns:
        dict: Results of the scraping operation
    """
    results = {
        'success': False,
        'restaurant_info': {},
        'pages_saved': 0,
        'total_pages_found': 0,
        'saved_files': [],
        'errors': []
    }
    
    try:
        # Construct URL
        base_url = "https://www.zomato.com"
        url = f"{base_url}/{city}/{restaurant_slug}/reviews"
        
        # Start session
        session = requests.Session()
        
        # Fetch initial page
        print(f"🔍 Fetching initial page: {url}")
        resp = fetch_page(url, session)
        
        if not resp or resp.status_code != 200:
            results['errors'].append(f"Failed to fetch initial page: {url}")
            return results
        
        # Parse initial page
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Get restaurant info
        restaurant_info = get_restaurant_info(soup)
        results['restaurant_info'] = restaurant_info
        
        # Clean restaurant name for directory
        clean_restaurant_name = clean_filename(restaurant_slug)
        
        # Use dynamic pagination discovery to get ALL pages
        print(f"🔄 Using dynamic pagination discovery to find all pages...")
        
        if max_pages:
            print(f"⚠️ Limiting to {max_pages} pages as requested")
        
        # Use the new dynamic pagination function
        dynamic_results = save_html_pages_dynamic(
            base_url=base_url,
            initial_url=url,
            restaurant=clean_restaurant_name,
            session=session,
            max_pages=max_pages
        )
        
        # Update results with dynamic pagination results
        results['pages_saved'] = dynamic_results['pages_saved']
        results['total_pages_found'] = dynamic_results['total_pages_found']
        results['saved_files'] = dynamic_results['saved_files']
        results['errors'].extend(dynamic_results['errors'])
        
        # Final results
        results['success'] = results['pages_saved'] > 0
        
        print(f"\n🎉 Scraping completed!")
        print(f"📊 Restaurant: {restaurant_info.get('name', restaurant_slug)}")
        print(f"📁 Directory: {base_dir}/zomato/restaurants/{clean_restaurant_name}/review_pages/")
        print(f"📄 Pages saved: {results['pages_saved']}/{results['total_pages_found']}")
        
        if results['errors']:
            print(f"⚠️ Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"   - {error}")
        
        logger.info(f"Scraping completed for {restaurant_slug}: {results['pages_saved']} pages saved")
        
    except Exception as e:
        results['errors'].append(f"Unexpected error: {e}")
        logger.error(f"Unexpected error in scrape_restaurant_reviews: {e}")
        print(f"💥 Unexpected error: {e}")
    
    return results


def scrape_multiple_restaurants(restaurants_list, base_dir="data/raw/html", max_pages_per_restaurant=None):
    """
    Scrape multiple restaurants in batch.
    
    Args:
        restaurants_list (list): List of tuples (city, restaurant_slug)
        base_dir (str): Base directory for saving files
        max_pages_per_restaurant (int, optional): Max pages per restaurant
        
    Returns:
        dict: Batch scraping results
    """
    batch_results = {
        'total_restaurants': len(restaurants_list),
        'successful_restaurants': 0,
        'total_pages_saved': 0,
        'individual_results': [],
        'errors': []
    }
    
    print(f"🚀 Starting batch scraping for {len(restaurants_list)} restaurants...")
    
    for i, (city, restaurant_slug) in enumerate(restaurants_list, 1):
        print(f"\n{'='*50}")
        print(f"🏪 [{i}/{len(restaurants_list)}] Processing: {restaurant_slug} in {city}")
        print(f"{'='*50}")
        
        try:
            result = scrape_restaurant_reviews(
                city=city,
                restaurant_slug=restaurant_slug,
                base_dir=base_dir,
                max_pages=max_pages_per_restaurant
            )
            
            batch_results['individual_results'].append(result)
            
            if result['success']:
                batch_results['successful_restaurants'] += 1
                batch_results['total_pages_saved'] += result['pages_saved']
            else:
                batch_results['errors'].extend(result['errors'])
                
        except Exception as e:
            error_msg = f"Error processing {restaurant_slug}: {e}"
            batch_results['errors'].append(error_msg)
            logger.error(error_msg)
            print(f"💥 {error_msg}")
    
    # Final batch summary
    print(f"\n{'='*60}")
    print(f"🎯 BATCH SCRAPING COMPLETED")
    print(f"{'='*60}")
    print(f"📊 Total restaurants processed: {batch_results['total_restaurants']}")
    print(f"✅ Successful restaurants: {batch_results['successful_restaurants']}")
    print(f"📄 Total pages saved: {batch_results['total_pages_saved']}")
    print(f"❌ Total errors: {len(batch_results['errors'])}")
    
    return batch_results


if __name__ == "__main__":
    # Example usage
    print("🔧 Testing Zomato Scraper...")
    
    # Single restaurant example
    result = scrape_restaurant_reviews(
        city="Pune",
        restaurant_slug="foo-kopa-mundhwa",
        max_pages=3  # Limit for testing
    )
    
    # Multiple restaurants example (commented out)
    # restaurants_to_scrape = [
    #     ("Pune", "foo-kopa-mundhwa"),
    #     ("Mumbai", "some-restaurant-slug"),
    #     ("Delhi", "another-restaurant-slug")
    # ]
    # 
    # batch_result = scrape_multiple_restaurants(
    #     restaurants_list=restaurants_to_scrape,
    #     max_pages_per_restaurant=2
    # )
