import os
import requests
import streamlit as st


st.set_page_config(page_title="Ask AI", page_icon="🧠")
st.title("Ask AI 🧠")
st.caption("Ask questions across feedback and knowledge base. Powered by RAG.")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


with st.form("ask_form"):
    query = st.text_input("Your question", placeholder="How do I reset my password?")
    top_k = st.number_input("Top K", min_value=1, max_value=20, value=5, step=1)
    submitted = st.form_submit_button("Ask")

if submitted:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            try:
                resp = requests.get(f"{BACKEND_URL}/rag/ask", params={"query": query, "top_k": top_k}, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                st.subheader("Answer")
                st.write(data.get("answer", ""))

                sources = data.get("sources", [])
                if sources:
                    st.subheader("Sources")
                    for i, s in enumerate(sources, start=1):
                        with st.expander(f"Source {i}: {s.get('title')}"):
                            st.json(s)
                else:
                    st.info("No sources returned.")
            except requests.HTTPError as e:
                st.error(f"Backend error: {e.response.text}")
            except Exception as e:
                st.error(f"Error: {e}")


