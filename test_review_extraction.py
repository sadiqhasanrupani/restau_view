#!/usr/bin/env python3
"""
Test script to verify review extraction from HTML file
"""

import sys
import os
from bs4 import BeautifulSoup

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'data'))

from scrape_zomato_review_phase_2 import extract_reviews_with_multiple_selectors

def test_review_extraction():
    """Test the review extraction function with the HTML file"""
    
    # Read the HTML file
    html_file_path = "data/raw/debug/page_2_source.html"
    
    if not os.path.exists(html_file_path):
        print(f"Error: HTML file not found at {html_file_path}")
        return
    
    print(f"Reading HTML file: {html_file_path}")
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract reviews
    print("Extracting reviews...")
    reviews = extract_reviews_with_multiple_selectors(soup, "Feast - Sheraton Grand")
    
    print(f"\nFound {len(reviews)} reviews")
    print("\n" + "="*80)
    
    # Display the extracted reviews
    for i, review in enumerate(reviews[:5], 1):  # Show first 5 reviews
        print(f"\nReview {i}:")
        print(f"  Restaurant: {review['restaurant_name']}")
        print(f"  Reviewer: {review['reviewer']}")
        print(f"  Rating: {review['rating']}")
        print(f"  Rating Type: {review['rating_type']}")
        print(f"  Date: {review['date']}")
        print(f"  Review Text: {review['review_text'][:100]}{'...' if len(review['review_text']) > 100 else ''}")
        print(f"  Extraction Method: {review['extraction_method']}")
        print("-" * 40)
    
    # Summary statistics
    if reviews:
        print(f"\nSummary:")
        print(f"  Total reviews: {len(reviews)}")
        print(f"  Reviews with ratings: {sum(1 for r in reviews if r['rating'] != 'N/A')}")
        print(f"  Reviews with dates: {sum(1 for r in reviews if r['date'] != 'N/A')}")
        print(f"  Reviews with text: {sum(1 for r in reviews if r['review_text'] != 'N/A' and len(r['review_text']) > 10)}")
        
        # Show unique rating types
        rating_types = set(r['rating_type'] for r in reviews)
        print(f"  Rating types found: {rating_types}")
        
        # Show unique dates
        dates = set(r['date'] for r in reviews if r['date'] != 'N/A')
        print(f"  Sample dates: {list(dates)[:5]}")

if __name__ == "__main__":
    test_review_extraction() 