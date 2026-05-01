import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def analyze_listings(listings: list[dict], user_criteria: dict) -> str:
    if not OPENROUTER_API_KEY:
        return "Missing OPENROUTER_API_KEY in .env"

    compact_listings = []

    for index, item in enumerate(listings, start=1):
        compact_listings.append({
            "id": index,
            "title": item.get("title"),
            "price": item.get("price"),
            "posted": item.get("posted"),
            "description": item.get("description", "")[:800],
            "source_url": item.get("source_url"),
        })

    prompt = f"""
You are an AI business acquisition analyst.

User criteria:
{json.dumps(user_criteria, indent=2)}

Business listings:
{json.dumps(compact_listings, indent=2)}

Tasks:
1. Rank the top 5 listings.
2. For each recommendation, make the business title a Markdown link using this format:
   ## 1. [Business Title](source_url)
3. Do not create a separate "Listing Links" section.
4. Do not add separate "Details" links.
5. Do not use raw HTML.
6. Do not use math formatting.
7. Do not add more texts or paragraphs outside of the recommendations.
8. Use $ consistently as a unit for prices.
9. For each recommendation, use this exact structure:

### 1. [Business Title](source_url)

**Price:** AUD price or Not listed

**Summary:** 1-2 sentence summary of the business.

**Why investigate:** Explain why it may match the buyer's criteria.

**Risks / missing info:** Mention unclear pricing, missing financials, franchise fees, rent, lease terms, owner involvement, or other risks.

Keep the output concise but useful.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )

    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]