# AI-Powered Business Opportunity Finder

This project is a Python-based tool that scrapes business listings from SEEK Business and uses AI to recommend opportunities worth investigating.

---

## Features

- Scrapes real business listings from SEEK Business
- Filters listings based on recent activity (≤ 7 days)
- Supports search by:
  - Keyword
  - Category
  - Location
- Extracts structured data:
  - Business name
  - Price
  - Description
  - Active since
- Uses AI (OpenRouter) to:
  - Rank top opportunities
  - Provide reasoning
  - Highlight risks and missing information
- Simple interactive UI built with Streamlit

---

## Tech Stack:
- Python 3.12+
- Streamlit (UI)
- BeautifulSoup + Requests (web scraping)
- OpenRouter API

---
## Setup Instructions:

1. Install dependencies
```bash
pip install -r requirements.txt
```

2. Insert your Openrouter API key inside `OPENROUTER_API_KEY` in the `.env` file

3. Run app

```bash
streamlit run app.py
```
