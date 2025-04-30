"""
Setup script for the yelp_scraper package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yelp_scraper",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for scraping business information from Yelp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yelp_scraper",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "asyncio",
        "beautifulsoup4>=4.10.0",
        "pandas>=1.3.0",
        "python-dotenv>=0.19.0",
        "pydantic>=1.9.0",
    ],
    entry_points={
        "console_scripts": [
            "yelp-scraper=yelp_scraper.cli:main",
        ],
    },
)
