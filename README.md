# RestauView: Zomato Restaurant Data Analysis Platform

## Overview
RestauView is a data analysis project focused on collecting, processing, and analyzing restaurant data from Zomato. The platform employs sophisticated web scraping techniques to extract comprehensive restaurant information, reviews, and ratings, then provides tools for data cleaning, analysis, and visualization.

## Features
- **Advanced Web Scraping**: Utilizes Selenium WebDriver with anti-detection measures to scrape restaurant data and reviews from Zomato
- **Multi-Source Data Extraction**: Combines data from HTML parsing and JSON-LD structured data for comprehensive information gathering
- **Robust Review Analysis**: Extracts reviewer names, ratings (including SVG star patterns), review text, dates, and distinguishes between dining and delivery reviews
- **Rating Detection Algorithms**: Uses multiple approaches to detect ratings (text patterns, SVG stars, numerical values) with fallback mechanisms
- **Complete Data Pipeline**: End-to-end process from scraping to cleaning to analysis
- **Debug Capabilities**: Comprehensive debugging tools and HTML saving for development and troubleshooting

## Project Structure
```
├── data/
│   ├── interim/           # Intermediate processed data
│   ├── processed/         # Final cleaned data ready for analysis
│   └── raw/               # Raw scraped data and debug HTML files
│       └── debug/         # HTML snippets for debugging extraction
├── notebooks/             # Jupyter notebooks for data exploration and visualization
├── reports/               # Generated analysis reports and visualizations
├── src/                   # Source code
│   ├── data/              # Data collection and preprocessing scripts
│   ├── models/            # Analysis models and algorithms
│   └── utils/             # Utility functions and helpers
└── tests/                 # Test scripts
```

## Installation

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser
- ChromeDriver compatible with your Chrome version

### Setup
1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/restau_view.git
   cd restau_view
   ```

2. Create a virtual environment (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Data Collection
To scrape restaurant data from Zomato:

```bash
python src/data/scrape_zomato.py
```

To scrape reviews for the collected restaurants:

```bash
python src/data/scrape_zomato_review_phase_2.py
```

For testing/development, set `DEMO_MODE = True` in the script to limit scraping to a few restaurants and reviews.

### Data Analysis
Jupyter notebooks in the `notebooks/` directory provide examples of data cleaning, analysis, and visualization:

```bash
jupyter notebook notebooks/data_cleaning.ipynb
```

## Key Components

### Scraping Module
- **scrape_zomato.py**: Collects basic restaurant information (name, URL, location, etc.)
- **scrape_zomato_review.py**: Initial review scraper
- **scrape_zomato_review_phase_2.py**: Enhanced review scraper with improved rating detection and anti-blocking features
- **single_zomato_Review_scrape.py**: For targeted scraping of specific restaurant reviews

### Preprocessing Module
- **preprocessing.py**: Data cleaning and preparation for analysis

## Anti-Detection Features
The scraper includes several features to avoid being blocked:
- Randomized user agents
- Stealth browser configurations
- Human-like scrolling patterns
- Random delays between actions
- Custom Chrome profile creation

## Rating Extraction Approaches
Multiple methods are used to extract ratings:
1. JSON-LD structured data extraction
2. Text pattern recognition
3. SVG star detection
4. Rating context analysis
5. Fallback mechanism for missing ratings

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Data source: [Zomato](https://www.zomato.com/)
- Project developed as part of a data analysis course/project