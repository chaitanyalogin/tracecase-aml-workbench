"""Deterministic calculations and evidence validation for synthetic AML exercises."""
from __future__ import annotations
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DECISIONS = {"close", "request_information", "escalate"}


def load_cases():
    cases = json.loads((ROOT / "data/cases.json").read_text(encoding="utf-8"))
    for case in cases:
        validate_case(case)
    return cases


def validate_case(case):
    income = case["customer"]["expected_monthly_inr"]
    if type(income) is not int or income <= 0:
        raise ValueError("Expected monthly income must be positive integer INR")
    ids = [case["customer"]["id"]] + [x["id"] for x in case["transactions"] + case["documents"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evidence identifier")
    if case["period_start"] > case["period_end"]:
        raise ValueError("Invalid review period")
    known = set(ids)
    for tx in case["transactions"]:
        datetime.fromisoformat(tx["date"])
        if type(tx["amount_inr"]) is not int or tx["amount_inr"] <= 0:
            raise ValueError("Amounts must be positive integer INR")
        if tx["direction"] not in {"in", "out"}:
            raise ValueError("Invalid direction")
    for doc in case["documents"]:
        if not set(doc.get("transaction_ids", [])) <= known:
            raise ValueError("Document references unknown evidence")


def in_period(case):
    return [t for t in case["transactions"] if case["period_start"] <= t["date"][:10] <= case["period_end"]]


def analyze(case):
    """No learned model, probability or statutory threshold is used here."""
    txs = in_period(case)
    incoming = [t for t in txs if t["direction"] == "in"]
    outgoing = [t for t in txs if t["direction"] == "out"]
    nonroutine = [t for t in incoming if t["purpose"] != "salary"]
    inflow = sum(t["amount_inr"] for t in incoming)
    outflow = sum(t["amount_inr"] for t in outgoing)
    exceptional = sum(t["amount_inr"] for t in nonroutine)
    monthly = case["customer"]["expected_monthly_inr"]
    by_day = defaultdict(lambda: {"in": 0, "out": 0})
    for t in txs:
        by_day[t["date"][:10]][t["direction"]] += t["amount_inr"]
    # Observable temporal association only. Fungible funds cannot be traced from this alone.
    peak_ratio, peak_in, peak_out = 0.0, [], []
    for day in sorted({t["date"][:10] for t in nonroutine}):
        end = (datetime.fromisoformat(day) + timedelta(days=1)).date().isoformat()
        ins = [t for t in nonroutine if t["date"][:10] == day]
        outs = [t for t in outgoing if day <= t["date"][:10] <= end]
        total = sum(t["amount_inr"] for t in ins)
        ratio = sum(t["amount_inr"] for t in outs) / total if total else 0
        if ratio > peak_ratio:
            peak_ratio, peak_in, peak_out = ratio, ins, outs
    facts = [
        {"id": "F001", "claim": f"Review-period credits total INR {inflow:,}; debits total INR {outflow:,}.", "evidence_ids": [t["id"] for t in txs]},
        {"id": "F002", "claim": f"Non-salary credits total INR {exceptional:,}, {exceptional / monthly:.1f} times declared monthly income of INR {monthly:,}.", "evidence_ids": [case["customer"]["id"]] + [t["id"] for t in nonroutine]},
        {"id": "F003", "claim": f"Non-salary credits involve {len({t['counterparty_id'] for t in nonroutine})} distinct counterparties.", "evidence_ids": [t["id"] for t in nonroutine]},
    ]
    if peak_in:
        facts.append({"id": "F004", "claim": f"The largest observed same-day/next-day debit-to-non-salary-credit ratio is {peak_ratio:.1%}. This is temporal proximity, not proof that the same funds were transferred.", "evidence_ids": [t["id"] for t in peak_in + peak_out]})
    return {"inflow_inr": inflow, "outflow_inr": outflow, "non_salary_inr": exceptional,
            "income_multiple": exceptional / monthly, "counterparties": len({t["counterparty_id"] for t in nonroutine}),
            "rapid_ratio": peak_ratio, "daily": dict(sorted(by_day.items())), "facts": facts,
            "rule_version": "demo-1.0", "alert_basis": "Review non-routine credits above 10 times declared monthly income; review any closely following debits. These are illustrative training rules, not legal reporting thresholds."}


def evidence_map(case, analysis):
    return {x["id"]: x for x in [case["customer"]] + case["transactions"] + case["documents"] + analysis["facts"]}


def packet(case, analysis):
    return {"case_id": case["id"], "synthetic": True,
            "period": [case["period_start"], case["period_end"]],
            "customer": case["customer"], "transactions": case["transactions"],
            "documents": case["documents"], "computed_facts": analysis["facts"],
            "rule_version": analysis["rule_version"], "alert_basis": analysis["alert_basis"]}


def packet_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_brief(brief, known_ids):
    if not isinstance(brief, dict) or set(brief) != {"facts", "hypotheses", "questions", "recommendation", "rationale"}:
        raise ValueError("Use exactly: facts, hypotheses, questions, recommendation, rationale")
    if brief["recommendation"] not in DECISIONS:
        raise ValueError("Unknown recommendation")
    if not isinstance(brief["rationale"], str) or not brief["rationale"].strip():
        raise ValueError("Rationale is required")
    for field in ["facts", "hypotheses", "questions"]:
        if not isinstance(brief[field], list):
            raise ValueError(f"{field} must be an array")
    if not brief["facts"]:
        raise ValueError("At least one cited fact is required")
    for fact in brief["facts"]:
        if not isinstance(fact, dict) or set(fact) != {"claim", "evidence_ids"}:
            raise ValueError("Each fact requires claim and evidence_ids")
        if not isinstance(fact["claim"], str) or not fact["claim"].strip():
            raise ValueError("Empty fact")
        refs = fact["evidence_ids"]
        if not isinstance(refs, list) or not refs or any(not isinstance(x, str) for x in refs):
            raise ValueError("Each fact needs evidence identifiers")
        unknown = set(refs) - set(known_ids)
        if unknown:
            raise ValueError("Unknown evidence identifiers: " + ", ".join(sorted(unknown)))
    if any(not isinstance(x, str) for x in brief["hypotheses"] + brief["questions"]):
        raise ValueError("Hypotheses and questions must contain text")
    return brief


def decision_errors(decision, rationale, evidence_ids, known_ids, checks):
    errors = []
    if decision not in DECISIONS:
        errors.append("Choose an outcome")
    if len(rationale.split()) < 40:
        errors.append("Explain your decision in at least 40 words")
    if not evidence_ids or not set(evidence_ids) <= set(known_ids):
        errors.append("Select valid supporting evidence")
    if len(checks) != 4 or not all(checks):
        errors.append("Complete all four evidence and judgment checks")
    return errors
