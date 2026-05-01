from scraper import scrape_seek_business

listings = scrape_seek_business(
    keyword="cafe",
    category_key="",
    location_key="",
    max_pages=1,
    max_listings=5,
)

for item in listings:
    print("TITLE:", item["title"])
    print("PRICE:", item["price"])
    print("ACTIVE SINCE:", item["active_since"])
    print("IS RECENT:", item["is_recent"])
    print("URL:", item["source_url"])
    print("-" * 80)
