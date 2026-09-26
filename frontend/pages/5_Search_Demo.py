import os
import requests
import streamlit as st


st.set_page_config(page_title="Search Demo", page_icon="🔎")
st.title("Search Demo 🔎")
st.caption("Query the unified search index (feedback + KB)")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


with st.form("search_form"):
    query = st.text_input("Query", placeholder="password reset")
    top_k = st.number_input("Top K", min_value=1, max_value=50, value=10, step=1)
    submitted = st.form_submit_button("Search")

if submitted:
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Searching..."):
            try:
                resp = requests.get(f"{BACKEND_URL}/search/", params={"query": query, "top_k": top_k}, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                st.subheader("Results")
                st.json(data)
            except requests.HTTPError as e:
                st.error(f"Backend error: {e.response.text}")
            except Exception as e:
                st.error(f"Error: {e}")


