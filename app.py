"""Web version of the toolkit. Run locally with:  streamlit run app.py

On Streamlit Community Cloud, add your API key under Settings > Secrets, never in the code.
Every AI call uses the key owner's credits, so share the link with care or set APP_PASSWORD.
"""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from toolkit import assistant, consultation, starter, tender
from toolkit.llm import get_llm
from toolkit.retrieval import Library

load_dotenv()
try:  # Streamlit Cloud stores keys in st.secrets; copy them into the environment for toolkit.llm
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass  # running locally with a .env file instead

st.set_page_config(page_title="Strategy AI Toolkit", page_icon="🧭", layout="wide")
st.title("Strategy AI Toolkit")
st.caption(
    "AI-assisted research and reporting for outcomes-based strategy. Public documents and illustrative "
    "sample data only. Every output is a first draft for a consultant to review."
)

password = os.getenv("APP_PASSWORD")
if password and st.text_input("Password", type="password") != password:
    st.stop()


@st.cache_resource
def llm():
    return get_llm()


@st.cache_resource
def library():
    lib = Library()
    lib.add_folder("data/library")
    return lib


tab0, tab1, tab2, tab3 = st.tabs(["Tender Fit Checker", "Consultation Analyser", "Document Assistant", "Strategy Starter"])

with tab0:
    st.write("Checks a draft tender response against the tender's own scored criteria and lists gaps by marks at risk.")
    col1, col2 = st.columns(2)
    tender_text = col1.text_area("Tender: requirements and award criteria", Path("data/sample_tender.txt").read_text(), height=360)
    draft_text = col2.text_area("Draft response", Path("data/sample_draft.txt").read_text(), height=360)
    if st.button("Check the draft", type="primary"):
        with st.spinner("Reviewing the draft against each criterion..."):
            md = tender.to_markdown(tender.check(tender_text, draft_text, llm()))
        st.markdown(md)
        st.download_button("Download as Markdown", md, "tender_fit_check.md")

with tab1:
    st.write("Groups responses into themes and checks every quote word for word against its source.")
    question = st.text_input("Consultation question", "What should a national health and social care regulator prioritise over the next three years?")
    sample = pd.read_csv("data/sample_responses.csv")
    uploaded = st.file_uploader("Or upload your own CSV with a 'response' column", type="csv")
    df = pd.read_csv(uploaded) if uploaded else sample
    responses = [str(r).strip() for r in df["response"].dropna() if str(r).strip()]
    with st.expander(f"{len(responses)} responses"):
        st.dataframe(pd.DataFrame({"ID": [f"R{i}" for i in range(1, len(responses) + 1)], "Response": responses}), hide_index=True)
    if st.button("Find themes", type="primary"):
        with st.spinner("Reading responses..."):
            result = consultation.analyse(responses, llm(), question)
        for t in result["themes"]:
            q = t["quote"]
            st.subheader(f"{t['name']} ({t['count']} of {result['total_responses']})")
            st.write(t.get("description", ""))
            st.markdown(f"> “{q.get('text', '')}” (R{q.get('response_id')})")
            (st.success if q.get("verified") else st.error)("Quote verified" if q.get("verified") else "Quote not found in source")
            st.caption("Responses: " + ", ".join(f"R{i}" for i in t["response_ids"]))
        if result.get("less_common"):
            st.warning("Less common points to read by hand:\n\n" + "\n".join(f"- {p['point']} (R{p['response_id']})" for p in result["less_common"]))
        if result["unassigned"]:
            st.info("Not placed in any theme: " + ", ".join(f"R{i}" for i in result["unassigned"]))
        st.download_button("Download as Markdown", consultation.to_markdown(result, question), "consultation_analysis.md")

with tab2:
    lib = library()
    st.write(f"Answers from a library of {len(lib.passages)} passages and cites each point. Add PDFs to `data/library/` to extend it.")
    q = st.text_input("Question", "How will HIQA measure whether its plan is working?")
    if st.button("Ask the library", type="primary"):
        with st.spinner("Searching and answering..."):
            res = assistant.answer(q, lib, llm())
        st.markdown(res["answer"])
        if res["invalid_citations"]:
            st.error("Cites passages that were not retrieved: " + ", ".join(res["invalid_citations"]))
        st.subheader("Passages retrieved")
        for p in res["passages"]:
            st.markdown(f"**{p.id}** · {p.source} · {p.where}\n\n{p.text}")

with tab3:
    st.write("Turns a short intake form into a first-draft outcome strategy outline for consultant review.")
    example = json.loads(Path("data/sample_intake.json").read_text())
    intake = {k: st.text_area(label, example.get(k, ""), height=80) for k, label in starter.FIELDS.items()}
    if st.button("Draft the outline", type="primary"):
        with st.spinner("Drafting..."):
            md = starter.to_markdown(starter.draft(intake, llm()))
        st.markdown(md)
        st.download_button("Download as Markdown", md, "strategy_outline.md")
