"""
Body module: Contains all classes and data structures for the Yelp Scraper.
"""

import os
from dotenv import load_dotenv
load_dotenv()
from typing import Optional
from pydantic import BaseModel

# API Endpoints
YELP_SEARCH_ENDPOINT = "https://api.yelp.com/v3/businesses/search"
YELP_BUSINESS_ENDPOINT = "https://api.yelp.com/v3/businesses/{}"

# Check for API Key
YELP_API_KEY = os.getenv("YELP_API_KEY")

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {YELP_API_KEY}",
    "User-Agent": "Mozilla/5.0 (compatible; BusinessScraper/1.0)",
}

# Concurrent request limit
CONCURRENT_REQUESTS = 20

class Company(BaseModel):
    """Represents a business with its contact information."""
    company_name: str
    contact_name: Optional[str] = None
    company_email: str
    company_phone: Optional[str] = None
    address: Optional[str] = None
    summary: Optional[str] = None
    additional_info: Optional[str] = None
