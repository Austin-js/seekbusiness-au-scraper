from scraper import scrape_seek_business
from openrouter_client import analyze_listings

listings = scrape_seek_business(
    keyword="cafe",
    location_key="sydney",
    max_pages=3,
    max_listings=5,
)

criteria = {
    "preferred_business_type": "Cafe",
    "preferred_location": "Sydney",
    "max_budget": "$300,000",
    "goal": "Find affordable businesses worth investigating",
}

analysis = analyze_listings(listings, criteria)

print(analysis)