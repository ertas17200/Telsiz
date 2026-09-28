import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

val_spec = importlib.util.spec_from_file_location("validate_exam", ROOT / "scripts" / "validate_exam.py")
ve = importlib.util.module_from_spec(val_spec)
sys.modules["validate_exam"] = ve
assert val_spec.loader is not None
val_spec.loader.exec_module(ve)

sim_spec = importlib.util.spec_from_file_location("exam_simulator", ROOT / "scripts" / "exam_simulator.py")
sim = importlib.util.module_from_spec(sim_spec)
sys.modules["exam_simulator"] = sim
assert sim_spec.loader is not None
sim_spec.loader.exec_module(sim)

BANK = json.loads((ROOT / "academy" / "exam_questions.json").read_text("utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
RULES = json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))
CANDIDATES = json.loads((ROOT / "data" / "source_candidates.json").read_text("utf-8"))


def question(payload, qid):
    return next(q for q in payload["questions"] if q["id"] == qid)


class GroundedExamValidationTests(unittest.TestCase):
    def validate(self, payload=BANK, candidates=CANDIDATES):
        ve.validate_bank(payload, SOURCES, RULES, candidates)

    def mutate(self, qid, **changes):
        payload = copy.deepcopy(BANK)
        question(payload, qid).update(changes)
        return payload

    def test_repository_bank_is_valid(self):
        self.validate()

    def test_bank_must_remain_practice_only(self):
        payload = copy.deepcopy(BANK)
        payload["exam_status"] = "official"
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_duplicate_question_id_rejected(self):
        payload = copy.deepcopy(BANK)
        payload["questions"].append(copy.deepcopy(payload["questions"][0]))
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_pending_source_rejected(self):
        payload = self.mutate(
            "EXAM.TR.DUMMY-LOAD.001",
            source_ids=["TR.BTK.EHK.5809"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_rule_source_must_be_listed(self):
        payload = self.mutate(
            "EXAM.IARU.NATIONAL-RULES.001",
            source_ids=["IARU.R1.VHF.HANDBOOK.10.02"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_legal_question_rejects_amateur_source(self):
        payload = self.mutate(
            "EXAM.TR.DUMMY-LOAD.001",
            source_ids=["IARU.R1.BANDPLANS"],
            rule_ids=["IARU.R1.NATIONAL_RULES_PREVAIL"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_nonlegal_question_rejects_legal_rule(self):
        payload = self.mutate(
            "EXAM.IARU.NATIONAL-RULES.001",
            source_ids=["TR.BTK.FTM.TECH.2022-IK-SYD-245"],
            rule_ids=["TR.AMATEUR.DUMMY_LOAD"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_time_sensitive_question_rejected(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("EXAM.TR.DUMMY-LOAD.001", time_sensitive=True))

    def test_official_exam_claim_rejected(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("EXAM.TR.DUMMY-LOAD.001", official_exam_claim=True))

    def test_correct_option_must_exist(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("EXAM.TR.DUMMY-LOAD.001", correct_option_id="Z"))

    def test_source_grounded_candidate_ref_rejected(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate(
                "EXAM.TR.DUMMY-LOAD.001",
                candidate_refs=["CAND.COMMUNITY.ARCH-YUNUS.AMATOR-TELSIZ-REHBERI"],
            ))


class GroundedExamScoringTests(unittest.TestCase):
    def test_all_correct_scores_100(self):
        answers = {q["id"]: q["correct_option_id"] for q in BANK["questions"]}
        result = sim.score_answers(BANK, answers)
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["answered"], 4)
        self.assertEqual(result["correct"], 4)
        self.assertEqual(result["score_percent"], 100.0)

    def test_partial_answers_score_against_total_bank(self):
        first = BANK["questions"][0]
        result = sim.score_answers(BANK, {first["id"]: first["correct_option_id"]})
        self.assertEqual(result["answered"], 1)
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["unanswered"], 3)
        self.assertEqual(result["score_percent"], 25.0)

    def test_wrong_answer_is_not_counted_correct(self):
        first = BANK["questions"][0]
        wrong = next(o["id"] for o in first["options"] if o["id"] != first["correct_option_id"])
        result = sim.score_answers(BANK, {first["id"]: wrong})
        self.assertEqual(result["correct"], 0)

    def test_unknown_question_id_rejected(self):
        with self.assertRaises(ValueError):
            sim.score_answers(BANK, {"EXAM.DOES.NOT.EXIST": "A"})

    def test_invalid_option_id_rejected(self):
        with self.assertRaises(ValueError):
            sim.score_answers(BANK, {BANK["questions"][0]["id"]: "Z"})

    def test_duplicate_cli_answer_rejected(self):
        qid = BANK["questions"][0]["id"]
        with self.assertRaises(ValueError):
            sim.answers_from_pairs([(qid, "A"), (qid, "B")])


if __name__ == "__main__":
    unittest.main()
