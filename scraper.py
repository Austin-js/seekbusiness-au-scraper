import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode

BASE_URL = "https://www.seekbusiness.com.au"

CATEGORIES = {
    "Food & Drink": "within-food-and-drink",
    "Health, Beauthy & Fitness": "within-health-beauty-fitness",
    "Retail": "within-retail",
    "Commercial Services": "within-commercial-services",
    "Personal Services": "within-personal-services",
    "Cleaning & Maintenance": "within-cleaning-and-maintenance",
    "Accomodation, Tourism & Leisure": "within-accommodation-tourism-leisure",
    "Miscellaneous": "within-miscellaneous-industries",
}

LOCATIONS = {
    "Sydney (NSW)": "in-sydney-nsw",
    "Regional NSW": "in-regional-nsw",
    "Melbourne (VIC)": "in-melbourne-vic",
    "Regional Victoria": "in-regional-victoria",
    "Brisbane (QLD)": "in-brisbane-qld",
    "Gold Coast (QLD)": "in-gold-coast-qld",
    "Regional Queensland": "in-regional-qld",
    "Perth (WA)": "in-perth-wa",
    "Regional Western Australia": "in-regional-wa",
    "Adelaide (SA)": "in-adelaide-sa",
    "Regional South Australia": "in-regional-sa",
    "Hobart (TAS)": "in-hobart-tas",
    "Regional Tasmania": "in-regional-tas",
    "Canberra (ACT)": "in-act-act",
    "Darwin (NT)": "in-darwin-nt",
    "Regional Northern Territory": "in-regional-nt",
    "Rest of the World": "in-rest-of-the-world",
    "Auckland (NZ)": "in-auckland-nz",
    "Rest of New Zealand": "in-rest-of-new-zealand",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def get_soup(url: str) -> BeautifulSoup:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def build_search_url(keyword="", category_key="", location_key="", page=1):
    parts = [f"{BASE_URL}/businesses-for-sale"]

    if category_key:
        parts.append(CATEGORIES[category_key])

    if location_key:
        parts.append(LOCATIONS[location_key])

    url = "/".join(parts)

    query = {}
    if keyword:
        query["k"] = keyword
    if page > 1:
        query["pg"] = page

    if query:
        url = f"{url}?{urlencode(query)}"

    return url


def extract_price(soup: BeautifulSoup, fallback_text: str = "") -> str:
    price_tag = soup.find("p", class_="sbus-investment-text")

    if price_tag:
        text = clean_text(price_tag.get_text(separator=" "))

        if "$" in text:
            return text

    return "Not listed"


def extract_summary(soup: BeautifulSoup) -> str:
    summary_tag = soup.find("p", class_="infoSummary")

    if summary_tag:
        return clean_text(summary_tag.get_text(separator=" "))

    return ""


def extract_posted_text(text: str) -> str:
    match = re.search(
        r"\bnow\b|\btoday\b|\d+\s+minutes?\s+ago|\d+\s+hours?\s+ago|\d+\s+days?\s+ago",
        text,
        re.I,
    )
    return clean_text(match.group(0)) if match else ""


def extract_listing_links_from_search(search_url: str) -> list[str]:
    soup = get_soup(search_url)
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"]

        if "/business-listing/" in href:
            full_url = urljoin(BASE_URL, href.split("?")[0])
            if full_url not in links:
                links.append(full_url)

    return links


def extract_active_since(soup: BeautifulSoup) -> str:
    container = soup.find("div", class_="sbus-active-since")

    if not container:
        return ""

    h1 = container.find("h1")
    if not h1:
        return ""

    return clean_text(h1.get_text(separator=" "))


def is_recent(active_text: str) -> bool:
    if not active_text:
        return False

    text = active_text.lower()

    if any(value in text for value in ["today", "yesterday", "minute", "hour"]):
        return True

    match = re.search(r"(\d+)\s+day", text)

    if match:
        return int(match.group(1)) <= 7

    return False


def normalize_for_dedupe(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_listing_fingerprint(listing: dict) -> str:
    title = normalize_for_dedupe(listing.get("title", ""))
    description = normalize_for_dedupe(listing.get("description", ""))

    return f"{title}|{description[:300]}"


def scrape_listing_detail(url: str) -> dict:
    soup = get_soup(url)

    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(separator=" ")) if title_tag else ""

    active_since = extract_active_since(soup)

    page_text = soup.get_text(separator="\n")
    clean_page_text = clean_text(page_text)

    summary = extract_summary(soup)

    return {
        "title": title,
        "price": extract_price(soup, clean_page_text),
        "active_since": active_since,
        "is_recent": is_recent(active_since),
        "description": summary or clean_page_text[:1000],
        "source_url": url,
    }


def scrape_seek_business(
    keyword="",
    category_key="",
    location_key="",
    max_listings=10,
    max_pages_safety_limit=20,
):
    listings = []
    seen_links = set()
    seen_fingerprints = set()

    page = 1

    while len(listings) < max_listings and page <= max_pages_safety_limit:
        search_url = build_search_url(keyword, category_key, location_key, page)
        print(f"Searching page {page}: {search_url}")

        try:
            links = extract_listing_links_from_search(search_url)
        except Exception as exc:
            print(f"Stopped: failed to load page {page}. Error: {exc}")
            break

        if not links:
            print(f"Stopped: no listing links found on page {page}")
            break

        new_links_found = 0

        for link in links:
            if len(listings) >= max_listings:
                break

            if link in seen_links:
                continue

            seen_links.add(link)
            new_links_found += 1

            print(f"Checking listing: {link}")

            try:
                listing = scrape_listing_detail(link)
            except Exception as exc:
                print(f"Skipped listing due to error: {exc}")
                continue

            if not listing.get("is_recent"):
                print("Skipped: older than 7 days")
                continue

            fingerprint = get_listing_fingerprint(listing)

            if fingerprint in seen_fingerprints:
                print("Skipped: duplicate listing")
                continue

            seen_fingerprints.add(fingerprint)

            listings.append(listing)
            print(f"Added recent listing ({len(listings)}/{max_listings})")

        if new_links_found == 0:
            print(f"Stopped: no new listing links found on page {page}")
            break

        page += 1

    return listings
