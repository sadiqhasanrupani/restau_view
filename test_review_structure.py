#!/usr/bin/env python3
"""
Test script to examine the complete review structure
"""

import os
from bs4 import BeautifulSoup
import re

def test_review_structure():
    """Test the complete review structure"""
    
    # Read the HTML file
    html_file_path = "data/raw/debug/page_1_source.html"
    
    if not os.path.exists(html_file_path):
        print(f"Error: HTML file not found at {html_file_path}")
        return
    
    print(f"Reading HTML file: {html_file_path}")
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("Examining review structure...")
    
    # Find all review sections
    review_sections = soup.find_all('section', class_='sc-dENsGg')
    print(f"\nFound {len(review_sections)} review sections")
    
    for i, section in enumerate(review_sections[:3]):
        print(f"\n=== Review Section {i+1} ===")
        
        # Print the complete HTML of this section
        print("Complete HTML:")
        print(section.prettify()[:1000])  # First 1000 chars
        
        # Look for all elements with fKvqMN class within this section
        fkvqmn_elements = section.find_all(class_='fKvqMN')
        print(f"\nElements with fKvqMN class in section {i+1}:")
        for j, elem in enumerate(fkvqmn_elements):
            text = elem.get_text(strip=True)
            classes = ' '.join(elem.get('class', []))
            print(f"  {j+1}. Classes: {classes}")
            print(f"     Text: {text}")
        
        # Look for all paragraph elements
        paragraphs = section.find_all('p')
        print(f"\nParagraph elements in section {i+1}:")
        for j, p in enumerate(paragraphs):
            text = p.get_text(strip=True)
            classes = ' '.join(p.get('class', []))
            print(f"  {j+1}. Classes: {classes}")
            print(f"     Text: {text}")
        
        # Look for all span elements
        spans = section.find_all('span')
        print(f"\nSpan elements in section {i+1}:")
        for j, span in enumerate(spans):
            text = span.get_text(strip=True)
            classes = ' '.join(span.get('class', []))
            if text and len(text) < 100:  # Only show short text
                print(f"  {j+1}. Classes: {classes}")
                print(f"     Text: {text}")
        
        # Look for all div elements
        divs = section.find_all('div')
        print(f"\nDiv elements in section {i+1} (showing only those with text):")
        for j, div in enumerate(divs):
            text = div.get_text(strip=True)
            classes = ' '.join(div.get('class', []))
            if text and len(text) < 100 and not text.isdigit():  # Only show short text, not just numbers
                print(f"  {j+1}. Classes: {classes}")
                print(f"     Text: {text}")

if __name__ == "__main__":
    test_review_structure() 