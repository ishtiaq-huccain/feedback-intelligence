import os
import streamlit as st
import requests
import pandas as pd
from datetime import date

# -------------------------------
# Config
# -------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Feedback Intelligence Dashboard",
    layout="wide",
)

st.title("📊 Feedback Intelligence Dashboard")

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.header("Filters")

# Date range filter (returns list of dates)
date_range = st.sidebar.date_input("Select Date Range", [])
product = st.sidebar.text_input("Product (optional)")
locale = st.sidebar.text_input("Locale (optional)")
version = st.sidebar.text_input("Version (optional)")

# Build params EXACTLY matching FastAPI signature
params = {}
if date_range and len(date_range) == 2:
    params["start"] = date_range[0].strftime("%Y-%m-%d")
    params["end"] = date_range[1].strftime("%Y-%m-%d")
if product:
    params["product"] = product
if locale:
    params["locale"] = locale
if version:
    params["version"] = version

# -------------------------------
# Helper: Cached API Call
# -------------------------------
@st.cache_data(ttl=300)
def fetch_api(endpoint: str, query_params: dict = None):
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", params=query_params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API call failed: {e}")
        return None

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["KPIs", "Trends", "Drilldown", "Export"])

# -------------------------------
# KPIs
# -------------------------------
with tab1:
    st.subheader("Key Metrics")

    kpis = fetch_api("/analytics/kpis", params)
    if kpis:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Feedback", kpis.get("total_feedback", 0))
        col2.metric("% Negative", f"{kpis.get('percent_negative', 0):.2f}%")
        col3.metric("Top Category", kpis.get("top_categories", [{}])[0].get("category", "N/A"))
        col4.metric("Top Aspect", kpis.get("top_aspects", [{}])[0].get("aspect", "N/A"))
    else:
        st.info("No KPI data available.")

# -------------------------------
# Trends
# -------------------------------
with tab2:
    st.subheader("Trends Over Time")

    # Sentiment Trend
    sent = fetch_api("/analytics/trends/sentiment", params)
    if sent:
        df_sent = pd.DataFrame.from_dict(sent, orient="index").reset_index()
        df_sent.rename(columns={"index": "date"}, inplace=True)
        st.line_chart(df_sent.set_index("date")[["positive", "negative", "neutral"]])
    else:
        st.info("No sentiment trend data available.")

    # Category Trend
    cat = fetch_api("/analytics/trends/categories", params)
    if cat:
        df_cat = pd.DataFrame.from_dict(cat, orient="index").reset_index()
        df_cat.rename(columns={"index": "date"}, inplace=True)
        st.area_chart(df_cat.set_index("date"))
    else:
        st.info("No category trend data available.")

# -------------------------------
# Drilldown
# -------------------------------
with tab3:
    st.subheader("Drilldown: Representative Feedback")

    selected_category = st.selectbox(
        "Select Category",
        ["All", "Bug", "Feature Request", "Complaint", "Praise", 
         "Usability", "Documentation", "Performance", "Pricing", "Support", "Security"]
    )

    drill_params = params.copy()
    if selected_category != "All":
        drill_params["category"] = selected_category

    drill_data = fetch_api("/analytics/drilldown", drill_params)

    if drill_data and drill_data.get("results"):
        df = pd.DataFrame(drill_data["results"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No drilldown data available.")

# -------------------------------
# Export
# -------------------------------
with tab4:
    st.subheader("Export Filtered Data")

    try:
        resp = requests.get(f"{BACKEND_URL}/analytics/drilldown/export", params=params, timeout=20)
        if resp.status_code == 200:
            st.download_button(
                label="⬇️ Download CSV",
                data=resp.content,
                file_name="feedback_export.csv",
                mime="text/csv"
            )
        else:
            st.error(f"⚠️ Export failed: {resp.status_code} - {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error exporting CSV: {e}")
