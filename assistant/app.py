"""Demo UI:  streamlit run assistant/app.py"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st

from assistant.core import UnsafeSQL, ask

EXAMPLES = [
    "What is the total revenue at risk from customer churn?",
    "Which 5 products lost the most money to cancellations?",
    "How many customers are in each RFM segment, and what revenue do they bring?",
    "Show monthly net revenue for 2011",
]

st.set_page_config(page_title="Retail Revenue Rescue · Ask the data", page_icon="📊")
st.title("Ask the data")
st.caption("Questions are turned into read-only SQL over governed gold tables. Every answer shows its query.")

cols = st.columns(2)
for i, ex in enumerate(EXAMPLES):
    if cols[i % 2].button(ex, use_container_width=True):
        st.session_state.q = ex

question = st.text_input("Your question", key="q")
if question:
    with st.spinner("Thinking…"):
        try:
            result = ask(question)
        except UnsafeSQL as exc:
            st.error(f"Blocked by the safety guard: {exc}")
            st.stop()
        except Exception as exc:
            st.error(f"Couldn't answer that: {exc}")
            st.stop()
    st.markdown(result["answer"])
    data = result["data"]
    if data.shape[1] == 2 and len(data) > 1 and data.dtypes.iloc[1].kind in "if":
        st.bar_chart(data, x=data.columns[0], y=data.columns[1])
    st.dataframe(data, use_container_width=True)
    with st.expander("SQL used"):
        st.code(result["sql"], language="sql")
