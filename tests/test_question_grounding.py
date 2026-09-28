"""Directive test questions -> rule -> source -> locator chain checks.

Each question maps to the rule IDs an answer must be grounded in. The test
fails if a rule disappears, loses verification, or its source/locator chain
breaks. ``coverage`` records whether the rule set fully answers the question
or only part of it; partial questions must not be answered as complete.
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}
RULES = {r["id"]: r for r in json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))["rules"]}
TABLE = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))

spec = importlib.util.spec_from_file_location("frequency_lookup", ROOT / "scripts" / "frequency_lookup.py")
fl = importlib.util.module_from_spec(spec)
sys.modules["frequency_lookup"] = fl
assert spec.loader is not None
spec.loader.exec_module(fl)

QUESTIONS = [
    ("C sınıfı belgeyle 145 MHz'te kaç watt kullanabilirim?", ["TR.AMATEUR.C_144_146_MAX_5W", "TR.AMATEUR.TECHNICAL_COMPLIANCE"], "partial"),
    ("433 MHz'te C sınıfı amatör telsizci kaç watt kullanabilir?", ["TR.AMATEUR.C_430_440_MAX_5W", "TR.AMATEUR.TECHNICAL_COMPLIANCE"], "partial"),
    ("IARU band planında bulunan her frekansta Türkiye'de yayın yapabilir miyim?", ["IARU.R1.NATIONAL_RULES_PREVAIL", "TR.AMATEUR.TECHNICAL_COMPLIANCE"], "covered"),
    ("B sınıfı amatör A sınıfı frekanslarını kullanabilir mi?", ["TR.AMATEUR.BC_SUPERVISED_USE"], "partial"),
    ("A sınıfı operatör gözetiminde B veya C sınıfı kullanıcı ne yapabilir?", ["TR.AMATEUR.BC_SUPERVISED_USE"], "covered"),
    ("Belgesi olmayan biri eğitim sırasında telsiz kullanabilir mi?", ["TR.AMATEUR.TRAINING_THIRD_PARTY"], "covered"),
    ("Şifreli haberleşme yapabilir miyim?", ["TR.AMATEUR.NO_OBSCURING_ENCRYPTION"], "covered"),
    ("Amatör role kurmak için BTK izni gerekir mi?", ["TR.AMATEUR.REPEATER_AND_EXPERIMENTAL"], "partial"),
    ("Dummy load ne zaman zorunlu?", ["TR.AMATEUR.DUMMY_LOAD"], "covered"),
    ("TRAC'taki band planı BTK düzenlemesinin yerine geçer mi?", ["IARU.R1.NATIONAL_RULES_PREVAIL", "TR.AMATEUR.TECHNICAL_COMPLIANCE"], "partial"),
]


class QuestionGroundingTests(unittest.TestCase):
    def test_every_question_resolves_to_verified_chain(self):
        for question, rule_ids, _ in QUESTIONS:
            for rule_id in rule_ids:
                with self.subTest(question=question, rule=rule_id):
                    rule = RULES.get(rule_id)
                    self.assertIsNotNone(rule, "rule missing")
                    self.assertEqual(rule["verification_status"], "verified")
                    source = SOURCES[rule["source_id"]]
                    self.assertEqual(source["verification_status"], "verified")
                    self.assertTrue(any(isinstance(v, str) and v for v in rule["source_locator"].values()))
                    if rule["authority"] == "legal":
                        self.assertEqual(source["source_type"], "official_legal")
                        self.assertEqual(source["legal_status"], "current")

    def test_amateur_publications_never_ground_legal_rules(self):
        for rule in RULES.values():
            if SOURCES[rule["source_id"]]["source_type"] == "amateur_association":
                self.assertNotEqual(rule["authority"], "legal", rule["id"])

    def test_power_questions_give_limit_without_legal_verdict(self):
        for freq in (145.0, 433.0):
            with self.subTest(freq=freq):
                result = fl.evaluate(TABLE, SOURCES, fl.Request(license_class="C", frequency_mhz=freq))
                self.assertEqual(
                    [(l["max_output_power"], l["power_unit"]) for l in result["known_limits"]],
                    [(5, "W")],
                )
                self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_partial_questions_stay_partial_while_table_is_partial(self):
        partial = [q for q, _, coverage in QUESTIONS if coverage == "partial"]
        self.assertTrue(partial)
        self.assertEqual(TABLE["coverage_status"], "partial")


if __name__ == "__main__":
    unittest.main()
