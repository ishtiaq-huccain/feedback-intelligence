import os
import streamlit as st
import requests

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

st.title("Welcome to Feedback Intelligence")
st.write("Use the sidebar to navigate through ingestion, analytics, search, and ask pages.")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

with st.container():
    st.subheader("Backend health check")
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=3)
        st.json(r.json())
    except Exception as e:
        st.error(f"Backend not reachable: {e}")
