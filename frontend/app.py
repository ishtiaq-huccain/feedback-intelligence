import os
import streamlit as st


def _apply_streamlit_secrets() -> None:
    """Expose Streamlit Cloud secrets as env vars for pages that use os.getenv."""
    try:
        backend_url = st.secrets.get("BACKEND_URL")
    except (FileNotFoundError, AttributeError):
        backend_url = None
    if backend_url:
        os.environ.setdefault("BACKEND_URL", str(backend_url))


_apply_streamlit_secrets()

st.set_page_config(page_title="Feedback Intelligence", page_icon="📊", layout="wide")

st.title("Feedback Intelligence Dashboard")
st.caption("Navigate via the sidebar to ingest data, run analytics, search, and ask questions.")

st.markdown(
    """
    - Use Ingest pages to upload feedback and knowledge base documents.
    - Use Analytics to view trends and summaries.
    - Use Search to retrieve similar items from the unified index.
    - Use Ask AI / Agent to ask complex questions across data.
    """
)

st.info("Open the left sidebar to switch between pages.")


