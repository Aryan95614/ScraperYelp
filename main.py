"""
Yelp Scraper - Test Script

This script demonstrates how to use the Yelp Scraper to search for businesses
and extract their contact information.

Usage:
    python main.py

Make sure to set your YELP_API_KEY environment variable before running.
"""

import asyncio
import logging
import os
import sys
from typing import List

# Import from our reorganized modules
from body import Company
from func import scrape, export_csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def run_scraper(query: str, max_results: int = 50) -> List[Company]:
    """Run the scraper with the given search query."""
    logger.info(f"Starting scrape for query: '{query}' (max results: {max_results})")
    
    # Check if API key is available
    if not os.getenv("YELP_API_KEY"):
        logger.error("YELP_API_KEY environment variable is not set! Please set it before running.")
        return []
    
    try:
        # Run the scraper
        companies = await scrape(query, max_results)
        logger.info(f"Found {len(companies)} companies with contact information")
        return companies
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        return []


async def main():
    """Interactive CLI for the Yelp Scraper."""
    print("\n====== Yelp Scraper ======\n")

    # Prompt user for search query
    query = input("Enter search query (e.g., 'bakeries in Chicago IL'): ").strip()
    if not query:
        print("No query provided. Exiting.")
        return

    # Prompt user for maximum results
    max_results_input = input("Enter max number of results to collect (default 50): ").strip()
    if max_results_input.isdigit() and int(max_results_input) > 0:
        max_results = int(max_results_input)
    else:
        max_results = 50

    # Run the scraper
    companies = await run_scraper(query, max_results)

    # Display some results
    if companies:
        print(f"\nFound {len(companies)} businesses with contact information:")
        for i, company in enumerate(companies[:5], 1):  # Show first 5 results
            print(f"\n{i}. {company.company_name}")
            print(f"   Email: {company.company_email}")
            print(f"   Phone: {company.company_phone}")
            print(f"   Address: {company.address}")

        if len(companies) > 5:
            print(f"\n... and {len(companies) - 5} more.")

        # Ask whether to export
        export_choice = input("\nExport all results to CSV? (y/N): ").strip().lower()
        if export_choice == "y":
            csv_file = export_csv(companies, query)
            if csv_file:
                print(f"\nResults exported to: {csv_file}")
    else:
        print("\nNo businesses found or there was an error. Check the logs for details.")

    print("\n==============================\n")


if __name__ == "__main__":
    # Set a sample API key for testing (replace with your actual Yelp API key)
    if not os.getenv("YELP_API_KEY"):
        print("\n⚠️ No YELP_API_KEY found in environment variables.")
        print("Please set your API key before running, for example:")
        print("\nOn Windows:")
        print("set YELP_API_KEY=your_api_key_here")
        print("\nOn PowerShell:")
        print("$env:YELP_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    # Run the async main function
    asyncio.run(main())
