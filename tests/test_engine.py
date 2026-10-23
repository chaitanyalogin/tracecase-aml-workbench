import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine import analyze, decision_errors, evidence_map, load_cases, packet, packet_hash, validate_brief, validate_case
from ai_assistant import export_prompt, generate_brief, worked_example
from reporting import investigation_markdown
from storage import history, save_decision


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases()

    def test_review_period_excludes_old_salary(self):
        a, b = [analyze(c) for c in self.cases]
        self.assertEqual(a["inflow_inr"], 1230000)
        self.assertEqual(b["inflow_inr"], 1240000)
        self.assertEqual(a["outflow_inr"], 1154500)
        self.assertEqual(a["non_salary_inr"], 1200000)
        self.assertEqual(a["income_multiple"], 40)
        self.assertEqual(b["income_multiple"], 30)
        self.assertAlmostEqual(a["rapid_ratio"], .95)
        self.assertAlmostEqual(b["rapid_ratio"], .95)

    def test_distinct_counterparties(self):
        self.assertEqual(analyze(self.cases[0])["counterparties"], 10)
        self.assertEqual(analyze(self.cases[1])["counterparties"], 2)

    def test_duplicate_negative_and_zero_income_rejected(self):
        for mutation in ["duplicate", "negative", "zero"]:
            c = copy.deepcopy(self.cases[0])
            if mutation == "duplicate":
                c["transactions"].append(c["transactions"][0])
            elif mutation == "negative":
                c["transactions"][0]["amount_inr"] = -1
            else:
                c["customer"]["expected_monthly_inr"] = 0
            with self.assertRaises(ValueError):
                validate_case(c)

    def test_evidence_packet_has_no_coaching_answers(self):
        data = packet(self.cases[0], analyze(self.cases[0]))
        prompt = export_prompt(data)
        self.assertNotIn("reasonable_outcomes", prompt)
        self.assertNotIn("coach", data)
        changed = copy.deepcopy(data)
        changed["documents"][0]["text"] += " new evidence"
        self.assertNotEqual(packet_hash(data), packet_hash(changed))

    def test_unknown_citations_and_invalid_recommendation_rejected(self):
        known = evidence_map(self.cases[0], analyze(self.cases[0]))
        brief = {"facts": [{"claim": "Test", "evidence_ids": ["MISSING"]}], "hypotheses": [], "questions": [], "recommendation": "close", "rationale": "Test"}
        with self.assertRaisesRegex(ValueError, "Unknown evidence"):
            validate_brief(brief, known)
        brief["facts"][0]["evidence_ids"] = ["F001"]
        brief["recommendation"] = "block_account"
        with self.assertRaisesRegex(ValueError, "Unknown recommendation"):
            validate_brief(brief, known)
        brief["recommendation"] = "request_information"
        self.assertEqual(validate_brief(brief, known), brief)

    def test_empty_ai_facts_and_unknown_keys_rejected(self):
        brief = {"facts": [], "hypotheses": [], "questions": [], "recommendation": "close", "rationale": "Test"}
        with self.assertRaises(ValueError):
            validate_brief(brief, ["F001"])
        brief["secret"] = "extra"
        with self.assertRaises(ValueError):
            validate_brief(brief, ["F001"])

    def test_live_model_adapter_uses_schema_and_no_automatic_actions(self):
        from types import SimpleNamespace
        known = evidence_map(self.cases[0], analyze(self.cases[0]))
        brief = {"facts": [{"claim": "Credits total INR 1,230,000.", "evidence_ids": ["F001"]}], "hypotheses": ["Unverified collections for friends"], "questions": ["What supports the explanation?"], "recommendation": "request_information", "rationale": "The explanation lacks corroboration."}
        fake = SimpleNamespace(status="completed", output_text=json.dumps(brief), id="test-response", usage=None)
        with patch("openai.OpenAI") as client:
            api = client.return_value.__enter__.return_value
            api.responses.create.return_value = fake
            result = generate_brief(packet(self.cases[0], analyze(self.cases[0])), known, "test-only", "test-model")
            self.assertEqual(result["brief"], brief)
            args = api.responses.create.call_args.kwargs
            self.assertFalse(args["store"])
            self.assertTrue(args["text"]["format"]["strict"])
            self.assertNotIn("tools", args)
            fake.status = "incomplete"
            with self.assertRaises(ValueError):
                generate_brief({}, known, "test-only", "test-model")

    def test_decision_requires_evidence_and_review(self):
        errors = decision_errors("close", "too short", [], {"F001": {}}, [False] * 4)
        self.assertEqual(len(errors), 3)
        self.assertFalse(decision_errors("close", "reason " * 41, ["F001"], {"F001": {}}, [True] * 4))

    def test_history_is_case_scoped_and_preserves_prior_record(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"TRACECASE_DB": str(Path(tmp) / "events.sqlite3")}):
            save_decision("C001", {"outcome": "request_information"})
            save_decision("C001", {"outcome": "escalate"})
            save_decision("C002", {"outcome": "close"})
            self.assertEqual([x["outcome"] for x in history("C001")], ["escalate", "request_information"])
            self.assertEqual(len(history("C002")), 1)

    def test_public_sessions_cannot_read_or_change_each_others_history(self):
        visitor_a, visitor_b = {}, {}
        payload = {"outcome": "request_information", "evidence_ids": ["F001"]}
        save_decision("C001", payload, session=visitor_a)
        payload["evidence_ids"].append("F002")
        self.assertEqual(history("C001", session=visitor_b), [])
        result = history("C001", session=visitor_a)
        self.assertEqual(result[0]["evidence_ids"], ["F001"])
        result[0]["evidence_ids"].append("FAKE")
        self.assertEqual(history("C001", session=visitor_a)[0]["evidence_ids"], ["F001"])

    def test_report_uses_saved_evidence_and_rejects_another_case(self):
        case = self.cases[0]
        snapshot = packet(case, analyze(case))
        event = {"case_id": case["id"], "packet_snapshot": snapshot,
                 "analyst": "Test analyst", "created_at": "2026-10-23T12:00:00Z",
                 "outcome": "request_information", "rationale": "Unverified explanation needs corroboration.",
                 "evidence_ids": ["F002"], "packet_hash": packet_hash(snapshot),
                 "exercise_policy": "TraceCase training policy 1.0"}
        report = investigation_markdown(case, event)
        self.assertIn(event["rationale"], report)
        self.assertIn(event["packet_hash"], report)
        self.assertIn("not a regulatory filing", report)
        with self.assertRaises(ValueError):
            investigation_markdown(self.cases[1], event)

    def test_worked_example_is_grounded_but_does_not_claim_to_be_live_ai(self):
        for case in self.cases:
            data = packet(case, analyze(case))
            brief = validate_brief(worked_example(data), evidence_map(case, analyze(case)))
            self.assertIn("not an answer key", brief["rationale"])
            self.assertEqual(brief["facts"][0]["claim"], data["computed_facts"][0]["claim"])


if __name__ == "__main__":
    unittest.main()
