"""
Func module: Contains all functions for the Yelp Scraper.
"""

import asyncio
import csv
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from pydantic import ValidationError

from body import Company, HEADERS, YELP_SEARCH_ENDPOINT, YELP_BUSINESS_ENDPOINT, CONCURRENT_REQUESTS

logger = logging.getLogger(__name__)

# Regular expressions
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


# Utility functions
def slugify(text: str) -> str:
    """Simplify string to be filename friendly."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()


async def fetch_json(session: aiohttp.ClientSession, url: str, params: dict = None, headers: dict = None) -> Optional[dict]:
    """Fetch JSON with retries."""
    retries = 3
    backoff = 2
    for attempt in range(retries):
        try:
            async with session.get(url, params=params, headers=headers, timeout=20) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    logger.warning("Rate limited. Sleeping before retrying...")
                    await asyncio.sleep(backoff * (attempt + 1))
                else:
                    text = await resp.text()
                    logger.error("Failed to fetch %s (status %s): %s", url, resp.status, text[:200])
                    return None
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            logger.error("Error fetching %s: %s", url, e)
            await asyncio.sleep(backoff * (attempt + 1))
    return None


async def fetch_text(session: aiohttp.ClientSession, url: str, headers: dict = None) -> Optional[str]:
    """Fetch raw text/HTML from a URL."""
    try:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                return await resp.text()
            logger.debug("Failed to fetch %s: status %s", url, resp.status)
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        logger.debug("Error fetching %s: %s", url, e)
    return None


def extract_emails(text: str) -> Set[str]:
    """Extract email addresses from text."""
    return set(EMAIL_REGEX.findall(text))


def parse_query(query: str) -> tuple[str, str]:
    """Parse search query into term and location."""
    m = re.search(r"\s+in\s+(.+)$", query, flags=re.I)
    if m:
        location = m.group(1).strip()
        term = query[: m.start()].strip()
        if not term:
            term = "businesses"
    else:
        # Fallback: treat entire string as term; ask Yelp to guess location via IP
        term = query
        location = ""
    return term, location


# API functions
async def get_yelp_businesses(
    session: aiohttp.ClientSession, term: str, location: str, max_results: int = 500
) -> List[dict]:
    """Fetch businesses from Yelp API based on search term and location."""
    businesses = []
    offset = 0
    limit = 50  # Yelp API max per request
    
    while offset < max_results:
        params = {
            "term": term,
            "limit": min(limit, max_results - offset),
            "offset": offset,
        }
        if location:
            params["location"] = location
        
        logger.info(f"Fetching businesses for '{term}' in '{location}' (offset: {offset})")
        result = await fetch_json(session, YELP_SEARCH_ENDPOINT, params, headers=HEADERS)
        
        if not result or "businesses" not in result:
            break
        
        batch = result["businesses"]
        if not batch:
            break
        
        businesses.extend(batch)
        offset += len(batch)
        logger.info(f"Retrieved {len(businesses)}/{max_results} businesses")
        
        if len(batch) < limit:  # No more results
            break
    
    return businesses[:max_results]


async def get_business_details(session: aiohttp.ClientSession, business_id: str) -> Optional[dict]:
    """Fetch detailed information for a specific business from Yelp API."""
    url = YELP_BUSINESS_ENDPOINT.format(business_id)
    return await fetch_json(session, url, headers=HEADERS)


# Scraper functions
async def enrich_business_with_email(
    session: aiohttp.ClientSession, sem: asyncio.Semaphore, biz: dict
) -> Optional[Company]:
    """Scrape business details and extract email address."""
    business_id = biz.get("id")
    if not business_id:
        return None
    
    async with sem:
        logger.debug("Processing %s", biz.get("name"))
        
        # Extract information from Yelp page first
        summary = ""
        email_set: Set[str] = set()
        
        # Visit Yelp listing page
        yelp_url = biz.get("url")
        if yelp_url:
            html = await fetch_text(session, yelp_url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                
                # Try to extract business summary
                summary_elem = soup.select_one('[data-testid="business-description-container"]')
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)
                
                # Get email from yelp page if available
                email_set.update(extract_emails(html))
        
        # Try business website if no email found
        if not email_set and "url" in biz:
            website_url = None
            # Look for website URL in the business details
            if biz.get("website"):
                website_url = biz["website"]
            
            # Alternatively, scrape from Yelp page
            if not website_url and html:
                soup = BeautifulSoup(html, "html.parser")
                website_link = soup.select_one('a[href^="https://www.yelp.com/biz_redir"]')
                if website_link:
                    website_url = website_link.get("href")
            
            # Fetch and extract emails from website
            if website_url:
                html = await fetch_text(session, website_url)
                if html:
                    email_set.update(extract_emails(html))
        
        if not email_set:
            return None  # Discard business without email
        
        # Pick first email
        email = sorted(email_set)[0]
        
        try:
            company = Company(
                company_name=biz.get("name", ""),
                contact_name=None,
                company_email=email,
                company_phone=biz.get("phone"),
                address=", ".join(filter(None, [
                    biz.get("location", {}).get("address1"),
                    biz.get("location", {}).get("city"),
                    biz.get("location", {}).get("state"),
                    biz.get("location", {}).get("zip_code"),
                ])),
                summary=summary,
                additional_info=f"Yelp URL: {biz.get('url')}"
            )
            return company
        except ValidationError as e:
            logger.debug("Validation error for %s: %s", biz.get("name"), e)
            return None


async def scrape(query: str, max_results: int = 500) -> List[Company]:
    """Main scraping routine."""
    term, location = parse_query(query)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Fetch business list
        businesses = await get_yelp_businesses(session, term, location, max_results=max_results * 2)
        if not businesses:
            logger.error("No businesses retrieved for query %s", query)
            return []
        
        # Step 2: Enrich each business concurrently
        sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
        tasks = [enrich_business_with_email(session, sem, b) for b in businesses]
        results = await asyncio.gather(*tasks)
        
        # Step 3: Filter & deduplicate
        deduped: Dict[Tuple[str, str], Company] = {}
        for comp in filter(None, results):
            key = (comp.company_name.lower(), comp.company_email.split("@")[-1].lower())
            if key not in deduped:
                deduped[key] = comp
            if len(deduped) >= max_results:
                break
        
        logger.info("Collected %s unique businesses with email", len(deduped))
        return list(deduped.values())


# CSV Export function
def export_csv(companies: List[Company], query: str) -> str:
    """Export companies to a CSV file."""
    if not companies:
        logger.warning("No companies to export.")
        return ""
    
    # Convert companies to DataFrame
    df = pd.DataFrame([c.dict() for c in companies])
    
    # Generate unique filename based on query and timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"scraped_{slugify(query)}_{timestamp}.csv"
    
    # Export to CSV
    df.to_csv(filename, index=False, quoting=csv.QUOTE_ALL)
    logger.info("Exported %s companies to %s", len(df), filename)
    
    return filename
