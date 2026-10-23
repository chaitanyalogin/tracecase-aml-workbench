import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class AppFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"TRACECASE_DB": str(Path(self.tmp.name) / "history.sqlite3"), "OPENAI_API_KEY": "", "OPENAI_MODEL": "", "TRACECASE_STORAGE": "session", "TRACECASE_ENABLE_LIVE_AI": "0"})
        self.env.start()
        self.at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_first_render_and_case_switch(self):
        self.assertFalse(self.at.exception)
        self.assertEqual(self.at.metric[0].value, "₹1,230,000")
        self.at.selectbox(key="case_select").select("C002").run()
        self.assertFalse(self.at.exception)
        self.assertEqual(self.at.metric[0].value, "₹1,240,000")
        self.assertTrue(self.at.button(key="live_C002").disabled)

    def test_invalid_ai_citation_is_visible_error(self):
        brief = {"facts": [{"claim": "Test", "evidence_ids": ["FAKE"]}], "hypotheses": [], "questions": [], "recommendation": "close", "rationale": "Test"}
        self.at.text_area(key="import_C001").set_value(json.dumps(brief))
        self.at.button(key="import_button_C001").click().run()
        self.assertFalse(self.at.exception)
        self.assertTrue(any("Unknown evidence" in x.value for x in self.at.error))

    def test_reviewed_case_save_and_case_isolation(self):
        at = self.at
        at.text_input(key="analyst_C001").set_value("Learner")
        at.selectbox(key="outcome_C001").select("request_information")
        at.text_area(key="rationale_C001").set_value("The incoming transfers differ from the declared salary-only profile. The customer claims to collect money for friends, but supporting agreements and the relationships between the parties remain undocumented. I would request corroborating records and complete relevant screening before determining whether the concern can be resolved or needs internal escalation.")
        at.multiselect(key="evidence_C001").select("F002").select("C001-D001")
        for i in range(4):
            at.checkbox(key=f"quality_C001_{i}").check()
        next(b for b in at.button if b.label == "Save reviewed decision").click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any("saved" in x.value for x in at.success))
        self.assertTrue(any("Coaching:" in e.label for e in at.expander))
        self.assertFalse((Path(self.tmp.name) / "history.sqlite3").exists())
        second_visitor = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assertFalse(any("Coaching:" in e.label for e in second_visitor.expander))
        at.selectbox(key="case_select").select("C002").run()
        self.assertFalse(at.exception)
        self.assertFalse(any("Coaching:" in e.label for e in at.expander))

    def test_ai_assisted_decision_requires_claim_review(self):
        at = self.at
        brief = {"facts": [{"claim": "Credits total INR 1,230,000.", "evidence_ids": ["F001"]}], "hypotheses": ["The transfers may have a legitimate explanation."], "questions": ["What documents support the explanation?"], "recommendation": "request_information", "rationale": "The customer's explanation is unverified."}
        at.text_area(key="import_C001").set_value(json.dumps(brief))
        at.button(key="import_button_C001").click().run()
        self.assertFalse(at.exception)
        at.text_input(key="analyst_C001").set_value("Learner")
        at.selectbox(key="outcome_C001").select("request_information")
        at.text_area(key="rationale_C001").set_value("The customer's activity differs from the salary-only profile and the explanation has not been corroborated. I would request evidence of the purpose of the collections and the relationships between all relevant parties. The AI suggestion is only a draft and does not establish criminal activity or replace review of the underlying evidence.")
        at.multiselect(key="evidence_C001").select("F001").select("C001-D001")
        at.checkbox(key="used_ai_C001").check()
        for i in range(4):
            at.checkbox(key=f"quality_C001_{i}").check()
        next(b for b in at.button if b.label == "Save reviewed decision").click().run()
        self.assertTrue(any("every AI factual claim" in x.value for x in at.error))
        self.assertFalse(any("Coaching:" in e.label for e in at.expander))
        next(c for c in at.checkbox if c.label == "I checked this claim against its evidence").check()
        next(b for b in at.button if b.label == "Save reviewed decision").click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any("saved" in x.value for x in at.success))

    def test_server_api_secret_is_never_prefilled_in_browser(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-server-secret-not-a-real-key"}):
            fresh = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
            self.assertEqual(fresh.text_input(key="api_key").value, "")
            self.assertTrue(fresh.button(key="live_C001").disabled)


if __name__ == "__main__":
    unittest.main()
