"""
Zomato Scraper Usage Examples
============================

This file contains examples of how to use the Zomato scraper module
for different scenarios.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.zomato_scraper import scrape_restaurant_reviews, scrape_multiple_restaurants


def example_single_restaurant():
    """
    Example: Scrape a single restaurant's reviews
    """
    print("="*60)
    print("📋 EXAMPLE 1: Single Restaurant Scraping")
    print("="*60)
    
    result = scrape_restaurant_reviews(
        city="Pune",
        restaurant_slug="foo-kopa-mundhwa",
        base_dir="data/raw/html",
        max_pages=5  # Limit pages for testing
    )
    
    print(f"\n📊 Results Summary:")
    print(f"   Success: {result['success']}")
    print(f"   Restaurant: {result['restaurant_info'].get('name', 'Unknown')}")
    print(f"   Pages saved: {result['pages_saved']}")
    print(f"   Files: {len(result['saved_files'])}")
    
    return result


def example_multiple_restaurants():
    """
    Example: Scrape multiple restaurants in batch
    """
    print("="*60)
    print("📋 EXAMPLE 2: Batch Restaurant Scraping")
    print("="*60)
    
    # List of restaurants to scrape
    restaurants_to_scrape = [
        ("Pune", "foo-kopa-mundhwa"),
        # Add more restaurants here:
        # ("Mumbai", "restaurant-slug"),
        # ("Delhi", "another-restaurant"),
    ]
    
    batch_result = scrape_multiple_restaurants(
        restaurants_list=restaurants_to_scrape,
        base_dir="data/raw/html", 
        max_pages_per_restaurant=3  # Liimt pages per restaurant
    )
    
    print(f"\n📊 Batch Results Summary:")
    print(f"   Total restaurants: {batch_result['total_restaurants']}")
    print(f"   Successful: {batch_result['successful_restaurants']}")
    print(f"   Total pages saved: {batch_result['total_pages_saved']}")
    print(f"   Errors: {len(batch_result['errors'])}")
    
    return batch_result


def example_custom_directory():
    """
    Example: Use custom directory structure
    """
    print("="*60)
    print("📋 EXAMPLE 3: Custom Directory Structure")
    print("="*60)
    
    result = scrape_restaurant_reviews(
        city="Pune",
        restaurant_slug="foo-kopa-mundhwa",
        base_dir="custom_data/scraped_html",  # Custom directory
        max_pages=2
    )
    
    print(f"\n📁 Files saved in custom directory:")
    for file_path in result['saved_files']:
        print(f"   - {file_path}")
    
    return result


def main():
    """
    Run all examples
    """
    print("🚀 Starting Zomato Scraper Examples...\n")
    
    # Example 1: Single restaurant
    try:
        example_single_restaurant()
    except Exception as e:
        print(f"❌ Example 1 failed: {e}")
    
    print("\n" + "="*80 + "\n")
    
    # Example 2: Multiple restaurants (commented out for testing)
    # try:
    #     example_multiple_restaurants()
    # except Exception as e:
    #     print(f"❌ Example 2 failed: {e}")
    
    # Example 3: Custom directory
    try:
        example_custom_directory()
    except Exception as e:
        print(f"❌ Example 3 failed: {e}")
    
    print("\n🎉 Examples completed!")
    print("\n📁 Check the following directories for scraped files:")
    print("   - data/raw/html/zomato/restaurants/")
    print("   - custom_data/scraped_html/zomato/restaurants/")


if __name__ == "__main__":
    main()
