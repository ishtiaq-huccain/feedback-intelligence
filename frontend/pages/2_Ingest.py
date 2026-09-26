import os
import streamlit as st
import requests

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")  # adjust if backend is remote

st.title("📥 Feedback Ingestion")

uploaded_file = st.file_uploader("Upload feedback file (CSV/JSON)", type=["csv", "json"])

if uploaded_file is not None:
    if st.button("Ingest"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        with st.spinner("Ingesting..."):
            resp = requests.post(f"{API_URL}/ingest/feedback", files=files)
        if resp.status_code == 200:
            data = resp.json()
            st.success("Ingestion complete ✅")
            st.json(data)
        else:
            st.error(f"Error: {resp.text}")
