import os
import requests
import streamlit as st

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("📥 Ingest & Label")
st.caption("Upload feedback, generate labels, and embeddings.")

uploaded_file = st.file_uploader("Upload feedback file (CSV/JSON)", type=["csv", "json"])

col1, col2, col3 = st.columns(3)
with col1:
    ingest_clicked = st.button("Ingest Feedback")
with col2:
    label_clicked = st.button("Run Labeling")
with col3:
    embed_clicked = st.button("Generate Embeddings")

if ingest_clicked and uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    with st.spinner("Ingesting feedback..."):
        resp = requests.post(f"{API_URL}/ingest/feedback", files=files)
    if resp.status_code == 200:
        st.success("Ingestion complete ✅")
        st.json(resp.json())
    else:
        st.error(f"Error: {resp.text}")
elif ingest_clicked:
    st.warning("Please upload a file first.")

if label_clicked:
    with st.spinner("Running labeling batch..."):
        resp = requests.post(f"{API_URL}/labeling/batch")
    if resp.status_code == 200:
        st.success("Labeling complete ✅")
        st.json(resp.json())
    else:
        st.error(f"Error: {resp.text}")

if embed_clicked:
    with st.spinner("Generating embeddings for feedback..."):
        resp = requests.post(f"{API_URL}/embeddings/all")
    if resp.status_code == 200:
        st.success("Embeddings generated ✅")
        st.json(resp.json())
    else:
        st.error(f"Error: {resp.text}")
