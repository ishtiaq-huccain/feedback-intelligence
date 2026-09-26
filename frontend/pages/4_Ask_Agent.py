import os
import requests
import streamlit as st


st.set_page_config(page_title="Ask Agent", page_icon="🤖")
st.title("Ask Agent 🤖")
st.caption("Planner + Stats + RAG with citations.")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


with st.form("ask_agent_form"):
    query = st.text_input("Your question", placeholder="Why did sentiment drop in July?")
    submitted = st.form_submit_button("Ask")

if submitted:
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            try:
                resp = requests.get(f"{BACKEND_URL}/ask/agent", params={"query": query}, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                st.subheader("Answer")
                st.write(data.get("answer", ""))

                plan = data.get("plan", {})
                st.subheader("Plan")
                st.json(plan)

                stats = data.get("stats")
                if stats:
                    st.subheader("Stats")
                    st.json(stats)

                examples = data.get("examples")
                if examples:
                    st.subheader("Examples")
                    for ex in examples:
                        st.write(f"- {ex}")

                sources = data.get("sources", [])
                if sources:
                    st.subheader("Sources")
                    for i, s in enumerate(sources, start=1):
                        with st.expander(f"Source {i}: {s.get('title')}"):
                            st.json(s)
            except requests.HTTPError as e:
                st.error(f"Backend error: {e.response.text}")
            except Exception as e:
                st.error(f"Error: {e}")


