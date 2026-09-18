import streamlit as st
import pandas as pd

from data_loader import load_tickets
from nlq_engine import ask_question
from anomaly_detector import get_all_anomalies, HOURS_THRESHOLD

st.set_page_config(page_title="Support Ticket AI System", layout="wide")

@st.cache_data
def get_data():
    return load_tickets()


df = get_data()

st.title("🎫 Support Ticket AI System")
st.caption(f"{len(df)} tickets loaded — powered by a local LLM (Ollama)")

tab1, tab2 = st.tabs(["💬 Ask a Question", "🚨 Anomalies"])

with tab1:
    question = st.text_input(
        "Ask a question about the tickets",
        placeholder="e.g. Which agent has the lowest average customer rating?",
    )

    if question:
        with st.spinner("Thinking..."):
            result = ask_question(df, question)

        if result["success"]:
            answer = result["answer"]

            if isinstance(answer, (pd.DataFrame, pd.Series)):
                st.dataframe(answer)
            else:
                st.success(f"**Answer:** {answer}")

            with st.expander("Show generated pandas code"):
                st.code(result["generated_code"], language="python")
        else:
            st.error(result["error"])
            if "generated_code" in result:
                with st.expander("Show generated code (failed)"):
                    st.code(result["generated_code"], language="python")

with tab2:
    anomalies = get_all_anomalies(df)

    col1, col2 = st.columns(2)

    with col1:
        stale = anomalies["stale_high_priority"]
        st.metric(
            f"Stale High/Critical tickets (>{HOURS_THRESHOLD}h open)",
            stale["count"],
        )
        if stale["count"] > 0:
            st.dataframe(pd.DataFrame(stale["tickets"]))

    with col2:
        outliers = anomalies["resolution_time_outliers"]
        st.metric(
            f"Resolution time outliers (>{outliers['threshold_hours_used']}h)",
            outliers["count"],
        )
        if outliers["count"] > 0:
            st.dataframe(pd.DataFrame(outliers["tickets"]))