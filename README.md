# Yelp Scraper

A Python module for scraping business information from Yelp, including contact details and email addresses.

## Features

- Search for businesses using the Yelp Fusion API
- Extract business details including contact information
- Scrape email addresses from business websites
- Export results to CSV format
- Concurrent processing for faster scraping

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/yelp_scraper.git
cd yelp_scraper

# Install the package
pip install -e .
```

### Using pip

```bash
pip install yelp_scraper
```

## Configuration

Before using the scraper, you need to set up your Yelp Fusion API key. You can obtain a key by creating an app on the [Yelp Fusion API](https://www.yelp.com/developers/documentation/v3/authentication) page.

Create a `.env` file in your project directory with the following content:

```
YELP_API_KEY=your_yelp_api_key_here
```

Alternatively, you can set the environment variable directly:

```bash
export YELP_API_KEY=your_yelp_api_key_here  # Unix/Linux/MacOS
set YELP_API_KEY=your_yelp_api_key_here     # Windows Command Prompt
$env:YELP_API_KEY="your_yelp_api_key_here"  # Windows PowerShell
```

## Usage

### Command Line

```bash
# Basic usage
yelp-scraper "restaurants in New York NY"

# Limit results
yelp-scraper "cafes in Seattle WA" --max 100
```

### Python API

```python
import asyncio
from yelp_scraper import scrape, export_csv

# Example usage in an async function
async def main():
    # Search for businesses
    companies = await scrape("bakeries in Chicago IL", max_results=50)
    
    # Export to CSV
    csv_file = export_csv(companies, "bakeries in Chicago IL")
    print(f"Exported {len(companies)} companies to {csv_file}")

# Run the async function
asyncio.run(main())
```

## Project Structure

```
yelp_scraper/
├── yelp_scraper/
│   ├── __init__.py       # Package initialization
│   ├── api.py            # Yelp API interaction
│   ├── cli.py            # Command line interface
│   ├── csv_exporter.py   # CSV export functionality
│   ├── models.py         # Data models
│   ├── scrapers.py       # Web scraping functionality
│   └── utils.py          # Utility functions
├── tests/                # Test directory
│   └── __init__.py
├── README.md             # Project documentation
├── requirements.txt      # Package dependencies
└── setup.py              # Package setup script
```

## License

MIT
