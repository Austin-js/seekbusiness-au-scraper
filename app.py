import streamlit as st
import pandas as pd

from scraper import scrape_seek_business, CATEGORIES, LOCATIONS
from openrouter_client import analyze_listings


st.set_page_config(page_title="Business Opportunity Finder", layout="wide")

st.title("AI-Powered Business Opportunity Finder")
st.caption("Scrape, filter, and analyze SEEK Business listings using AI.")

with st.sidebar:
    st.header("Search Criteria")

    keyword = st.text_input("Keyword", value="")

    category_label = st.selectbox(
        "Category",
        ["Any"] + list(CATEGORIES.keys())
    )

    location_label = st.selectbox(
        "Location",
        ["Any"] + list(LOCATIONS.keys())
    )

    no_budget_limit = st.checkbox("No budget limit", value=False)

    max_budget = st.number_input(
        "Max Budget (AUD)",
        min_value=0,
        max_value=10_000_000,
        value=300_000,
        step=50_000,
        format="%d",
        disabled=no_budget_limit
    )

    if no_budget_limit:
        max_budget = None

    if max_budget:
        budget_text = f"${max_budget:,}"
    else:
        budget_text = "No limit"

    goal = st.text_area(
        "Buyer goal",
        value="Find affordable businesses worth investigating further."
    )

    max_listings = st.slider("Max recent listings", 1, 50, 10)

    search_button = st.button("Find Opportunities")


if search_button:
    category_key = "" if category_label == "Any" else category_label
    location_key = "" if location_label == "Any" else location_label

    with st.spinner("Scraping SEEK Business listings..."):
        listings = scrape_seek_business(
            keyword=keyword,
            category_key=category_key,
            location_key=location_key,
            max_listings=max_listings,
        )

    listings = sorted(
        listings,
        key=lambda x: (
            x.get("price") != "Not listed",
        ),
        reverse=True
    )
    st.success(f"Found {len(listings)} recent listings")

    if not listings:
        st.warning("No recent listings found. Try increasing pages scanned or changing filters.")
        st.stop()

    display_rows = []

    for index, item in enumerate(listings, start=1):
        display_rows.append({
            "#": index,
            "Business Name": item.get("title", ""),
            "Price": item.get("price", ""),
            "Active Since": item.get("active_since", ""),
            "Description": item.get("description", ""),
            "Link": item.get("source_url", ""),
        })

    df = pd.DataFrame(display_rows)

    st.subheader("Recent Listings Found")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Link"),
            "Description": st.column_config.TextColumn("Description", width="large"),
        },
    )

    user_criteria = {
        "keyword": keyword,
        "category": category_label,
        "location": location_label,
        "max_budget": max_budget,
        "goal": goal,
    }

    with st.spinner("Analyzing listings with OpenRouter..."):
        analysis = analyze_listings(listings, user_criteria)

    st.subheader("Top AI Recommendations")
    st.write(analysis)
