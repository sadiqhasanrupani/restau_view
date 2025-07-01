# Zomato Scraper - Modular System

A comprehensive, reusable system for scraping Zomato restaurant reviews with organized file storage and pagination handling.

## 🏗️ Directory Structure Created

```
data/
└── raw/
    └── html/
        └── zomato/
            └── restaurants/
                └── {restaurant_name}/
                    └── review_pages/
                        ├── page_1.html
                        ├── page_2.html
                        ├── page_3.html
                        └── ...
```

## 📁 Project Structure

```
src/
├── utils/
│   └── helpers.py              # Reusable utility functions
├── scrapers/
│   └── zomato_scraper.py       # Main scraper module
└── logger/                     # Log files directory

test/
└── extract_zomator_htmls.py    # Original test script (updated)

examples/
└── zomato_scraper_examples.py  # Usage examples

data/
└── raw/
    └── html/                   # Organized scraped files
```

## 🚀 Quick Start

### Single Restaurant Scraping

```python
from src.scrapers.zomato_scraper import scrape_restaurant_reviews

# Scrape a single restaurant
result = scrape_restaurant_reviews(
    city="Pune",
    restaurant_slug="foo-kopa-mundhwa",
    max_pages=5  # Optional: limit pages
)

print(f"Success: {result['success']}")
print(f"Pages saved: {result['pages_saved']}")
print(f"Files saved: {result['saved_files']}")
```

### Multiple Restaurants (Batch)

```python
from src.scrapers.zomato_scraper import scrape_multiple_restaurants

restaurants = [
    ("Pune", "foo-kopa-mundhwa"),
    ("Mumbai", "restaurant-slug"),
    ("Delhi", "another-restaurant")
]

batch_result = scrape_multiple_restaurants(
    restaurants_list=restaurants,
    max_pages_per_restaurant=3
)
```

### Custom Directory

```python
result = scrape_restaurant_reviews(
    city="Pune",
    restaurant_slug="foo-kopa-mundhwa",
    base_dir="custom_data/html",  # Custom base directory
    max_pages=2
)
```

## 🛠️ Functions Available

### Core Scraping Functions

| Function | Description |
|----------|-------------|
| `scrape_restaurant_reviews()` | Main function to scrape all review pages |
| `scrape_multiple_restaurants()` | Batch scrape multiple restaurants |
| `get_all_pages()` | Handle pagination and fetch all pages |
| `save_organized_files()` | Save files in organized structure |

### Utility Functions (from helpers.py)

| Function | Description |
|----------|-------------|
| `extract_zomato_pagination()` | Extract pagination links from HTML |
| `fetch_page()` | Fetch web page with headers and retry logic |
| `save_content()` | Save content to file with directory creation |
| `get_random_headers()` | Generate random browser headers |
| `random_sleep()` | Random delay to mimic human behavior |

### Information Extraction

| Function | Description |
|----------|-------------|
| `get_restaurant_info()` | Extract restaurant metadata (name, rating, cuisine) |
| `clean_filename()` | Clean strings for filesystem use |

## 📋 Usage Examples

### Example 1: Run Test Script
```bash
uv run test\extract_zomator_htmls.py
```

### Example 2: Use Scraper Module Directly
```bash
uv run src\scrapers\zomato_scraper.py
```

### Example 3: Run Examples
```bash
uv run examples\zomato_scraper_examples.py
```

## 🔧 Configuration Options

### Parameters

- **`city`**: City name (e.g., "Pune", "Mumbai")
- **`restaurant_slug`**: Restaurant URL identifier 
- **`base_dir`**: Base directory for saving files (default: "data/raw/html")
- **`max_pages`**: Maximum number of pages to scrape (optional)

### Output Structure

Each scraping operation creates:
- Organized directory structure
- Individual HTML files for each page
- Comprehensive logging
- Error handling and reporting

## 📊 Return Values

### scrape_restaurant_reviews() Returns:

```python
{
    'success': bool,
    'restaurant_info': {
        'name': str,
        'location': str,
        'cuisine': str,
        'rating': str
    },
    'pages_saved': int,
    'total_pages_found': int,
    'saved_files': [list of file paths],
    'errors': [list of error messages]
}
```

## 🔍 Features

### ✅ Implemented
- **Pagination Handling**: Automatically detects and follows pagination links
- **Organized Storage**: Creates structured directory hierarchy
- **Batch Processing**: Scrape multiple restaurants in one operation
- **Error Handling**: Comprehensive error reporting and logging
- **Rate Limiting**: Random delays to avoid being blocked
- **Flexible Configuration**: Customizable directories and limits
- **Restaurant Metadata**: Extracts name, rating, cuisine information
- **Logging System**: Detailed logs for debugging and monitoring

### 🔄 Reusable Components
- **Pagination extraction** can be used for any Zomato page
- **File organization** system works for any scraping project
- **HTTP utilities** (headers, delays, fetching) are generic
- **Logging system** can be used across the project

## 🚨 Error Handling

The system includes robust error handling:
- Network timeout and retry logic
- File system error handling
- Pagination parsing failures
- Invalid URL handling
- Graceful degradation when pages are missing

## 📝 Logging

All operations are logged to:
- `src/logger/zomato_scraper.log` - Main scraper logs
- `src/logger/extract_zomator_htmls.log` - Test script logs

## 🎯 Use Cases

1. **Research Projects**: Collect restaurant review data for analysis
2. **Market Research**: Analyze competitor reviews and ratings
3. **Data Science**: Build datasets for sentiment analysis
4. **Business Intelligence**: Track restaurant performance over time
5. **Academic Studies**: Restaurant industry research

## 🔧 Extending the System

### Adding New Sites
1. Create new scraper in `src/scrapers/`
2. Use existing utility functions from `helpers.py`
3. Follow the same organized directory structure

### Adding New Features
1. Extend the `get_restaurant_info()` function for more metadata
2. Add new pagination patterns to `extract_zomato_pagination()`
3. Create specialized utility functions in `helpers.py`

## 📈 Performance Considerations

- **Rate Limiting**: Random delays between requests (1.5-4 seconds)
- **Session Management**: Reuses HTTP connections
- **Memory Efficient**: Processes pages one at a time
- **Error Recovery**: Continues processing even if individual pages fail

## 🔒 Responsible Scraping

This system implements responsible scraping practices:
- Respectful request timing
- Proper headers to identify as legitimate browser
- Error handling to avoid overwhelming servers
- Logging for transparency and debugging

---

**Ready to use!** The modular system is now fully functional and can be used throughout your workspace for comprehensive Zomato data collection.
