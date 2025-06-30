#!/usr/bin/env python3
"""
Test script to verify HTML parsing and review extraction
"""

import os
from bs4 import BeautifulSoup
import re

def extract_reviews_from_html(html_content, restaurant_name="N/A"):
    """Extract reviews from HTML content using the identified class names"""
    soup = BeautifulSoup(html_content, 'html.parser')
    all_reviews = []
    
    # Use the correct selector for review sections based on HTML analysis
    review_selectors = [
        "section.sc-dENsGg",  # Main review container class from HTML analysis
        "div[class*='ReviewCard']",
        "section[class*='review']",
        ".sc-dENsGg",
    ]
    
    print(f"Trying {len(review_selectors)} different selectors...")
    
    for selector in review_selectors:
        review_sections = soup.select(selector)
        if review_sections:
            print(f"Found {len(review_sections)} reviews with selector: {selector}")
            
            for idx, section in enumerate(review_sections):
                try:
                    # Extract reviewer name using the correct class name from HTML analysis
                    reviewer_selectors = [
                        "p.sc-1hez2tp-0.sc-lenlpJ.dCAQIv",  # Specific class for reviewer names
                        "p.sc-1hez2tp-0.sc-lenlpJ",
                        "div.sc-kGYfcE div p",
                    ]
                    
                    reviewer = "N/A"
                    for rev_sel in reviewer_selectors:
                        rev_elem = section.select_one(rev_sel)
                        if rev_elem and rev_elem.get_text(strip=True):
                            reviewer = rev_elem.get_text(strip=True)
                            break
                    
                    # Extract rating using the correct class name from HTML analysis
                    rating = "N/A"
                    rating_selectors = [
                        "div.sc-1q7bklc-1.cILgox",  # Specific class for rating number
                        "div.sc-1q7bklc-1",
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
                    
                    # Extract rating type using the correct class name from HTML analysis
                    rating_type = "DINING"  # Default to DINING
                    rating_type_selectors = [
                        "div.sc-1q7bklc-9.dYrjiw",  # Specific class for rating type
                        "div.sc-1q7bklc-9",
                    ]
                    
                    for type_sel in rating_type_selectors:
                        type_elem = section.select_one(type_sel)
                        if type_elem and type_elem.get_text(strip=True):
                            rating_type = type_elem.get_text(strip=True)
                            break
                    
                    # Extract post date using the correct class name from HTML analysis
                    date = "N/A"
                    date_selectors = [
                        "p.sc-1hez2tp-0.fKvqMN.time-stamp",  # Specific class for timestamps
                        "p.sc-1hez2tp-0.fKvqMN",
                        "p[class*='time-stamp']",
                    ]
                    
                    for date_sel in date_selectors:
                        try:
                            date_elem = section.select_one(date_sel)
                            if date_elem and date_elem.get_text(strip=True):
                                date_text = date_elem.get_text(strip=True)
                                # Skip if it contains irrelevant text
                                skip_words = ["vote", "comment", "helpful", "like", "share", "report"]
                                if not any(word in date_text.lower() for word in skip_words):
                                    # Check if it looks like a date
                                    date_patterns = ["ago", "day", "week", "month", "year"]
                                    if any(pattern in date_text.lower() for pattern in date_patterns):
                                        date = date_text
                                        break
                        except Exception as e:
                            continue
                    
                    # Extract review text
                    text_selectors = [
                        "p.sc-1hez2tp-0.sc-hfLElm.hreYiP",  # Specific class for review text
                        "p.sc-1hez2tp-0.sc-hfLElm",
                    ]
                    
                    review_text = "N/A"
                    for text_sel in text_selectors:
                        text_elem = section.select_one(text_sel)
                        if text_elem and len(text_elem.get_text(strip=True)) > 10:
                            review_text = text_elem.get_text(strip=True)
                            break
                    
                    # Only add if we have meaningful data
                    if (reviewer != "N/A" or rating != "N/A" or 
                        (review_text != "N/A" and len(review_text) > 5)):
                        all_reviews.append({
                            "restaurant_name": restaurant_name,
                            "reviewer": reviewer,
                            "rating": rating,
                            "rating_type": rating_type,
                            "review_text": review_text,
                            "date": date,
                            "extraction_method": selector,
                        })
                
                except Exception as e:
                    print(f"Error parsing review {idx + 1}: {e}")
                    continue
            
            # If we found reviews, break out of the loop
            if all_reviews:
                break
    
    return all_reviews

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
    
    # Extract reviews
    print("Extracting reviews...")
    reviews = extract_reviews_from_html(html_content, "Feast - Sheraton Grand")
    
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