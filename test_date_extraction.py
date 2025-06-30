#!/usr/bin/env python3
"""
Test script to examine HTML structure and find date elements
"""

import os
from bs4 import BeautifulSoup
import re

def test_date_extraction():
    """Test different date extraction methods"""
    
    # Read the HTML file
    html_file_path = "data/raw/debug/page_1_source.html"
    
    if not os.path.exists(html_file_path):
        print(f"Error: HTML file not found at {html_file_path}")
        return
    
    print(f"Reading HTML file: {html_file_path}")
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("Searching for date elements...")
    
    # Method 1: Search for time-stamp class
    print("\n1. Searching for 'time-stamp' class:")
    time_stamp_elements = soup.find_all(class_=re.compile(r'time-stamp'))
    for i, elem in enumerate(time_stamp_elements[:5]):
        print(f"  {i+1}. {elem.get_text(strip=True)}")
    
    # Method 2: Search for fKvqMN class
    print("\n2. Searching for 'fKvqMN' class:")
    fkvqmn_elements = soup.find_all(class_=re.compile(r'fKvqMN'))
    for i, elem in enumerate(fkvqmn_elements[:5]):
        print(f"  {i+1}. {elem.get_text(strip=True)}")
    
    # Method 3: Search for date-like patterns
    print("\n3. Searching for date-like patterns:")
    date_patterns = [
        r'\d+\s+days?\s+ago',
        r'\d+\s+weeks?\s+ago',
        r'\d+\s+months?\s+ago',
        r'\d+\s+years?\s+ago',
        r'one\s+month\s+ago',
        r'one\s+week\s+ago',
        r'one\s+day\s+ago',
        r'yesterday',
        r'today'
    ]
    
    all_text = soup.get_text()
    for pattern in date_patterns:
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        if matches:
            print(f"  Pattern '{pattern}': {matches[:3]}")
    
    # Method 4: Search for elements with color="#9C9C9C" (gray text often contains dates)
    print("\n4. Searching for gray text elements:")
    gray_elements = soup.find_all(attrs={'color': '#9C9C9C'})
    for i, elem in enumerate(gray_elements[:5]):
        text = elem.get_text(strip=True)
        if text and len(text) < 50:  # Only show short text
            print(f"  {i+1}. {text}")
    
    # Method 5: Search for any text containing "ago"
    print("\n5. Searching for text containing 'ago':")
    ago_elements = soup.find_all(text=re.compile(r'ago', re.IGNORECASE))
    for i, text in enumerate(ago_elements[:5]):
        if hasattr(text, 'strip'):
            text_str = text.strip()
            if text_str and len(text_str) < 100:
                print(f"  {i+1}. {text_str}")
    
    # Method 6: Look for specific review sections
    print("\n6. Examining review sections:")
    review_sections = soup.find_all('section', class_='sc-dENsGg')
    print(f"  Found {len(review_sections)} review sections")
    
    for i, section in enumerate(review_sections[:3]):
        print(f"\n  Review section {i+1}:")
        # Look for any paragraph elements
        paragraphs = section.find_all('p')
        for j, p in enumerate(paragraphs):
            text = p.get_text(strip=True)
            if text and len(text) < 100:
                classes = p.get('class', [])
                class_str = ' '.join(classes) if classes else 'no-class'
                print(f"    P{j+1} ({class_str}): {text}")

if __name__ == "__main__":
    test_date_extraction() 