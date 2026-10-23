"""TraceCase: a synthetic AML investigation workbench, milestone one."""
import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from ai_assistant import export_prompt, generate_brief, worked_example
from engine import (ROOT, analyze, decision_errors, evidence_map, in_period,
                    load_cases, packet, packet_hash, validate_brief)
from storage import history, save_decision
from reporting import investigation_markdown

st.set_page_config(page_title="TraceCase | AML Workbench", page_icon="🔎", layout="wide")
st.markdown("""<style>
.block-container {padding-top:2.2rem;max-width:1380px}
h1 {letter-spacing:-1.2px} h2,h3 {letter-spacing:-.4px}
[data-testid="stMetric"] {background:white;border:1px solid #dce5e9;border-radius:12px;padding:16px}
[data-testid="stSidebar"] {border-right:1px solid #dce5e9}
.eyebrow {color:#197c75;font-size:12px;letter-spacing:2px;font-weight:700}
.intro {font-size:17px;color:#546976;max-width:790px}
</style>""", unsafe_allow_html=True)

cases = load_cases()
# Session storage is the public-safe default. SQLite is an explicit local-only opt-in.
local_mode = os.getenv("TRACECASE_STORAGE", "session") == "local"
session_store = None if local_mode else st.session_state.setdefault("decision_history", {})
live_enabled = os.getenv("TRACECASE_ENABLE_LIVE_AI", "0") == "1"
with st.sidebar:
    st.markdown("### 🔎 TraceCase")
    st.caption("AML INVESTIGATION WORKBENCH")
    st.divider()
    case_id = st.selectbox("Investigation queue", [c["id"] for c in cases], format_func=lambda id: next(c["title"] for c in cases if c["id"] == id), key="case_select")
    st.info("Training environment • All people, transactions and documents are fictional.")
    with st.expander("Start here", expanded=True):
        st.write("1. Open Customer & evidence.\n2. Review calculated findings.\n3. Generate or import an AI brief.\n4. Verify its claims and record your decision.\n5. Compare with the coaching notes.")
    with st.expander("AML terms in plain English"):
        st.markdown("**KYC:** understand who the customer is.\n\n**CDD:** assess the relationship and expected activity.\n\n**EDD:** deeper checks when the risk needs them.\n\n**Alert:** a reason to review, not proof of crime.\n\n**Escalate:** refer unresolved concern to the appropriate reviewer.\n\n**Source of funds:** where the particular money came from.\n\n**PEP:** politically exposed person; the status alone does not establish wrongdoing.")
    st.caption("Local SQLite history" if local_mode else "Session demo: export your work before leaving. Other visitors do not share your history.")
    st.caption("Milestone 1.1 · Evidence before conclusions")

case = next(c for c in cases if c["id"] == case_id)
analysis = analyze(case)
evidence = evidence_map(case, analysis)
case_packet = packet(case, analysis)
digest = packet_hash(case_packet)
events = history(case_id, session=session_store)
st.markdown('<div class="eyebrow">INVESTIGATE · EXPLAIN · REVIEW</div>', unsafe_allow_html=True)
st.title("Follow the evidence.")
st.markdown('<div class="intro">Review an unusual transaction pattern, challenge the explanation and leave a decision another analyst can understand.</div>', unsafe_allow_html=True)
st.caption(f"{case_id} / {case['customer']['name']} / Review period {case['period_start']} to {case['period_end']} / INR")
cols = st.columns(4)
cols[0].metric("Period credits", f"₹{analysis['inflow_inr']:,}")
cols[1].metric("Non-salary credits", f"₹{analysis['non_salary_inr']:,}")
cols[2].metric("Vs declared monthly income", f"{analysis['income_multiple']:.1f}×")
cols[3].metric("Investigation", "Decision recorded" if events else "Awaiting review")
st.caption("Ratios describe the activity. They are not probabilities of crime or legal reporting thresholds.")
tabs = st.tabs(["Customer & evidence", "Transaction analysis", "AI assistance", "Decision & review"])

with tabs[0]:
    left, right = st.columns([1, 1.65])
    with left:
        st.subheader("Understand the customer")
        c = case["customer"]
        st.markdown(f"**{c['name']}**\n\n{c['occupation']}\n\nDeclared monthly income: **₹{c['expected_monthly_inr']:,}**\n\nDeclared source of funds: **{c['source_of_funds']}**\n\nRelationship since: {c['relationship_since']}\n\nEvidence: `{c['id']}`")
        st.warning("Check whether the activity has an economic explanation. A departure from expected activity opens a question; it does not answer it.")
    with right:
        st.subheader("Document register")
        for document in case["documents"]:
            with st.expander(f"{document['id']} | {document['title']}", expanded=True):
                st.caption(document["status"])
                st.write(document["text"])
                if document["transaction_ids"]:
                    st.caption("Related transactions: " + ", ".join(document["transaction_ids"]))

with tabs[1]:
    st.subheader("Calculated findings")
    st.info(analysis["alert_basis"])
    for fact in analysis["facts"]:
        st.markdown(f"**{fact['id']}** · {fact['claim']}")
        st.caption("Evidence: " + ", ".join(fact["evidence_ids"]))
    daily = pd.DataFrame.from_dict(analysis["daily"], orient="index").rename(columns={"in": "Credits", "out": "Debits"})
    st.bar_chart(daily, color=["#197C75", "#BD7156"])
    st.subheader("Transaction register")
    scope = st.radio("Show", ["Review period", "All supplied history"], horizontal=True, key=f"scope_{case_id}")
    txs = in_period(case) if scope == "Review period" else case["transactions"]
    direction = st.selectbox("Direction", ["All", "in", "out"], key=f"direction_{case_id}")
    visible = [t for t in txs if direction == "All" or t["direction"] == direction]
    frame = pd.DataFrame(visible)
    st.dataframe(frame, hide_index=True, width="stretch")
    st.download_button("Download these transactions", frame.to_csv(index=False), f"{case_id}_transactions.csv", "text/csv")
    st.caption("Transaction history is bounded to the supplied records. Absence of activity elsewhere is not established.")

with tabs[2]:
    st.subheader("Evidence linked assistance")
    st.write("Use the prepared prompt with ChatGPT and import the response. No model is called automatically.")
    prompt = export_prompt(case_packet)
    st.download_button("Download ChatGPT case prompt", prompt, f"{case_id}_ai_prompt.txt", "text/plain")
    st.download_button("Download evidence packet", json.dumps(case_packet, indent=2), f"{case_id}_packet.json", "application/json")
    st.caption("For a quick demonstration of claim review, load the author-written example below. It is not a live AI response or an answer key.")
    if st.button("Load author-written example brief", key=f"example_{case_id}"):
        brief = validate_brief(worked_example(case_packet), evidence)
        st.session_state[f"ai_{case_id}"] = {"brief": brief, "source": "Author-written worked example (not live AI)", "model": "None", "packet_hash": digest}
    with st.expander("How to use ChatGPT without an API key", expanded=True):
        st.write("Download the case prompt, open it, and paste its contents into ChatGPT. Ask for JSON only. Paste the returned JSON below, validate its references, then review every factual claim against the evidence. Your existing ChatGPT session is not an automatic connection to this application.")
    imported = st.text_area("Paste AI response JSON", height=130, key=f"import_{case_id}")
    if st.button("Validate and load response", key=f"import_button_{case_id}"):
        try:
            clean = imported.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.splitlines()[1:-1])
            brief = validate_brief(json.loads(clean), evidence)
            st.session_state[f"ai_{case_id}"] = {"brief": brief, "source": "User-imported AI response", "model": "Not independently verified", "packet_hash": digest}
            st.success("Schema and reference IDs validated. Claim accuracy still requires your review.")
        except (ValueError, TypeError, KeyError) as error:
            st.error(str(error))
    if not live_enabled:
        st.caption("Live API requests are disabled on this demo. Prompt export and response import work without an API key.")
    with st.expander("Optional live AI configuration", expanded=False):
        st.caption("For a deployment with live AI enabled, the synthetic case packet is sent to OpenAI only when you click Generate. API usage has separate billing. Keys are not written to case history.")
        # Never copy a server environment credential into a browser widget.
        api_key = st.text_input("OpenAI API key", type="password", key="api_key", value="", disabled=not live_enabled)
        model = st.text_input("Supported model ID from your API account", value=os.getenv("OPENAI_MODEL", ""), key="model_id", placeholder="Enter a model that supports structured outputs")
        consent = st.checkbox("Send this fictional evidence packet to OpenAI", key=f"consent_{case_id}")
        if st.button("Generate live AI brief", disabled=not (live_enabled and api_key and model.strip() and consent), key=f"live_{case_id}"):
            try:
                with st.spinner("Preparing a grounded case brief..."):
                    result = generate_brief(case_packet, evidence, api_key, model)
                    result["packet_hash"] = digest
                    st.session_state[f"ai_{case_id}"] = result
                st.success("Live response received. Review the evidence before using it.")
            except Exception:
                st.error("AI generation failed or the response could not be validated. Check your model, credentials, quota and connection. No case decision was made.")
    result = st.session_state.get(f"ai_{case_id}")
    if result and result.get("packet_hash") == digest:
        brief = result["brief"]
        st.divider()
        st.caption(f"Source: {result['source']} | Model: {result['model']} | Evidence snapshot: {digest[:12]}")
        st.warning("Validated reference IDs are not proof that a claim is accurate. Review the content of each cited record.")
        for index, fact in enumerate(brief["facts"]):
            st.write(fact["claim"])
            with st.expander("Inspect cited evidence: " + ", ".join(fact["evidence_ids"])):
                for ref in fact["evidence_ids"]:
                    st.json(evidence[ref])
            st.checkbox("I checked this claim against its evidence", key=f"checked_{case_id}_{digest}_{packet_hash(fact)}")
        st.markdown("**Possible interpretations, not established facts**")
        for hypothesis in brief["hypotheses"]:
            st.write("• " + hypothesis)
        st.markdown("**Information still needed**")
        for question in brief["questions"]:
            st.write("• " + question)
        st.markdown(f"**Suggested outcome:** {brief['recommendation'].replace('_', ' ')}")
        st.write(brief["rationale"])
        st.download_button("Download AI brief", json.dumps(result, indent=2), f"{case_id}_ai_brief.json", "application/json")
    else:
        st.info("No AI brief loaded for this case. The calculated findings and investigation workflow work without one.")

with tabs[3]:
    st.subheader("Record your investigation decision")
    st.write("Your decision can differ from the AI suggestion. Explain the evidence, alternatives and remaining uncertainty.")
    result = st.session_state.get(f"ai_{case_id}")
    if result and result.get("packet_hash") != digest:
        result = None
    with st.form(f"decision_{case_id}"):
        analyst = st.text_input("Analyst name or initials", key=f"analyst_{case_id}")
        decision = st.selectbox("Outcome", ["Select an outcome", "close", "request_information", "escalate"], format_func=lambda x: x.replace("_", " ").capitalize(), key=f"outcome_{case_id}")
        rationale = st.text_area("Investigation rationale, alternatives and limitations", height=150, key=f"rationale_{case_id}")
        selected = st.multiselect("Supporting evidence", list(evidence), key=f"evidence_{case_id}")
        use_ai = st.checkbox("I used the current AI brief in this decision", disabled=result is None, key=f"used_ai_{case_id}")
        checks = [st.checkbox(label, key=f"quality_{case_id}_{i}") for i, label in enumerate([
            "I verified the material amounts, dates and parties.",
            "I considered a legitimate explanation and contradictory evidence.",
            "I distinguished verified information from missing or unverified information.",
            "My decision and next steps follow the exercise policy, without asserting a crime is proven."])]
        submitted = st.form_submit_button("Save reviewed decision", type="primary")
    if submitted:
        errors = decision_errors(decision, rationale, selected, evidence, checks)
        if not analyst.strip():
            errors.append("Enter analyst initials or a name")
        if use_ai and result:
            if not all(st.session_state.get(f"checked_{case_id}_{digest}_{packet_hash(f)}", False) for f in result["brief"]["facts"]):
                errors.append("Review and acknowledge every AI factual claim in AI assistance")
        if errors:
            for error in errors:
                st.error(error)
        else:
            payload = {"analyst": analyst.strip(), "outcome": decision, "rationale": rationale,
                       "evidence_ids": selected, "quality_checks": checks, "packet_hash": digest,
                       "packet_snapshot": case_packet, "ai_assistance": result if use_ai else None,
                       "exercise_policy": "TraceCase training policy 1.0", "recorded_at": datetime.now(timezone.utc).isoformat()}
            event_id = save_decision(case_id, payload, session=session_store)
            st.success(f"Decision {event_id} saved. Open coaching below to compare your reasoning.")
            events = history(case_id, session=session_store)
    if events:
        st.subheader("Decision history")
        for event in events:
            with st.expander(f"Review {event['id']} | {event['outcome'].replace('_', ' ')} | {event['created_at']}"):
                st.write(event["rationale"])
                st.caption("Analyst: " + event["analyst"] + " | Evidence: " + ", ".join(event["evidence_ids"]))
        st.download_button("Export investigation history", json.dumps(events, indent=2), f"{case_id}_history.json", "application/json")
        st.download_button("Download latest investigation report", investigation_markdown(case, events[0]), f"{case_id}_investigation.md", "text/markdown")
        with st.expander("Coaching: compare your reasoning", expanded=False):
            coach = json.loads((ROOT / "data/coach.json").read_text())[case_id]
            st.caption("Author-written training guidance, not an independent expert assessment or live model result.")
            st.write(coach["reasoning"])
            st.markdown("**Avoid this mistake:** " + coach["pitfall"])
            for question in coach["questions"]:
                st.write("• " + question)
    else:
        st.info("Coaching notes become visible after your first reviewed decision.")
    with st.expander("Exercise policy and limitations"):
        st.write("Close an alert only when the supplied evidence reasonably explains it. Request information when material gaps can be resolved. Escalate unresolved concern or a material contradiction for internal review, explaining why. These are educational workflow conventions, not a jurisdiction-specific legal procedure. No report is filed and no account action is taken. There is no live sanctions or adverse-media feed, no independently validated risk model, no enterprise authentication and no multi-user reviewer approval. Local history is not tamper-proof and is not guaranteed to persist on ephemeral hosting.")
