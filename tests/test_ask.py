import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ask", ROOT / "scripts" / "ask.py")
ask = importlib.util.module_from_spec(spec)
sys.modules["ask"] = ask
assert spec.loader is not None
spec.loader.exec_module(ask)

KB = ask.Knowledge()

# The directive's reference questions and the rules each answer must cite.
DIRECTIVE_QUESTIONS = [
    ("C sınıfı belgeyle 145 MHz'te kaç watt kullanabilirim?", {"TR.AMATEUR.C_144_146_MAX_5W"}),
    ("433 MHz'te C sınıfı amatör telsizci kaç watt kullanabilir?", {"TR.AMATEUR.TECHNICAL_COMPLIANCE"}),
    ("IARU band planında bulunan her frekansta Türkiye'de yayın yapabilir miyim?",
     {"TR.AMATEUR.TECHNICAL_COMPLIANCE", "IARU.R1.NATIONAL_RULES_PREVAIL"}),
    ("B sınıfı amatör A sınıfı frekanslarını kullanabilir mi?",
     {"TR.AMATEUR.A_CLASS_USE", "TR.AMATEUR.BC_SUPERVISED_USE"}),
    ("A sınıfı operatör gözetiminde B veya C sınıfı kullanıcı ne yapabilir?", {"TR.AMATEUR.BC_SUPERVISED_USE"}),
    ("Belgesi olmayan biri eğitim sırasında telsiz kullanabilir mi?", {"TR.AMATEUR.TRAINING_THIRD_PARTY"}),
    ("Şifreli haberleşme yapabilir miyim?", {"TR.AMATEUR.NO_OBSCURING_ENCRYPTION"}),
    ("Amatör röle kurmak için BTK izni gerekir mi?", {"TR.AMATEUR.REPEATER_AND_EXPERIMENTAL"}),
    ("Dummy load ne zaman zorunlu?", {"TR.AMATEUR.DUMMY_LOAD"}),
    ("TRAC'taki band planı BTK düzenlemesinin yerine geçer mi?",
     {"TR.AMATEUR.TECHNICAL_COMPLIANCE", "IARU.R1.NATIONAL_RULES_PREVAIL"}),
]


def cited(result):
    return {i["rule_id"] for i in result["legal_basis"]} | {i["rule_id"] for i in result["amateur_practice"]}


class ParseTests(unittest.TestCase):
    def test_turkish_normalization(self):
        self.assertEqual(ask.normalize("İŞARET ŞİFRELİ Iğdır"), "isaret sifreli igdir")

    def test_frequency_units_and_decimal_comma(self):
        self.assertEqual(ask.parse("433,5 MHz")["frequencies_mhz"], [433.5])
        self.assertAlmostEqual(ask.parse("136 kHz")["frequencies_mhz"][0], 0.136)
        self.assertEqual(ask.parse("10,45 GHz")["frequencies_mhz"], [10450.0])

    def test_classes_power_and_basis(self):
        parsed = ask.parse("B sınıfı amatör A sınıfı ile 5 W e.i.r.p. kullanabilir mi?")
        self.assertEqual(parsed["license_classes"], ["B", "A"])
        self.assertEqual(parsed["requested_power_w"], 5)
        self.assertEqual(parsed["requested_power_basis"], "eirp")
        self.assertEqual(ask.parse("10 watt")["requested_power_basis"], "transmitter_output")

    def test_keywords_match_word_starts_only(self):
        self.assertFalse(ask._keyword_hit(ask.normalize("kontrol edebilir miyim"), "röle"))
        self.assertTrue(ask._keyword_hit(ask.normalize("röleye bağlanmak"), "röle"))


class DirectiveQuestionTests(unittest.TestCase):
    def test_every_directive_question_is_grounded(self):
        for question, expected in DIRECTIVE_QUESTIONS:
            with self.subTest(question=question):
                result = ask.answer(question, KB)
                self.assertFalse(result["fail_closed"])
                self.assertTrue(result["short_answer"])
                self.assertTrue(expected <= cited(result), cited(result))
                self.assertTrue(result["sources"])

    def test_c_145_mhz_gives_5w_without_blanket_permission(self):
        result = ask.answer(DIRECTIVE_QUESTIONS[0][0], KB)
        text = " ".join(result["short_answer"])
        self.assertIn("5 W (verici çıkış gücü)", text)
        self.assertIn("BİLİNMİYOR", text)
        self.assertIn("TR-BTK-EMISSION-001", result["open_source_conflicts"])

    def test_433_mhz_is_a_gap_and_points_to_nearest_subbands(self):
        result = ask.answer(DIRECTIVE_QUESTIONS[1][0], KB)
        text = " ".join(result["short_answer"])
        self.assertIn("listelenen bir aralıkta değil", text)
        self.assertIn("433,4–433,575 MHz (ham satır 22)", text)
        self.assertNotIn("TR.AMATEUR.C_430_440_MAX_5W", cited(result))

    def test_iaru_is_never_legal_basis(self):
        for question, _ in DIRECTIVE_QUESTIONS:
            with self.subTest(question=question):
                result = ask.answer(question, KB)
                self.assertNotIn("IARU.R1.NATIONAL_RULES_PREVAIL", {i["rule_id"] for i in result["legal_basis"]})


class VerdictTests(unittest.TestCase):
    def test_over_limit_is_a_clear_no(self):
        result = ask.answer("C sınıfı 145 MHz'te 10 W kullanabilir miyim?", KB)
        self.assertTrue(result["short_answer"][0].startswith("C sınıfı, 145 MHz: HAYIR"))

    def test_eirp_limit_needs_eirp_request(self):
        no = ask.answer("A sınıfı 136 kHz'te 5 W e.i.r.p. yayın", KB)["short_answer"][0]
        unknown = ask.answer("A sınıfı 136 kHz'te 5 W yayın", KB)["short_answer"][0]
        self.assertIn("HAYIR", no)
        self.assertIn("BİLİNMİYOR", unknown)

    def test_partial_table_never_renders_permission(self):
        for freq in ("0,136", "0,475", "5,36", "14,2", "51", "145", "431,6", "433", "1296"):
            for cls in "ABC":
                for power in ("", " 1 W", " 5 W", " 100 W"):
                    with self.subTest(freq=freq, cls=cls, power=power):
                        result = ask.answer(f"{cls} sınıfı {freq} MHz{power}", KB)
                        self.assertNotIn("izin var", " ".join(result["short_answer"]))

    def test_missing_class_lists_each_class(self):
        lines = ask.answer("145 MHz'te kaç watt?", KB)["short_answer"]
        self.assertTrue(any(line.startswith(f"{c} sınıfı, 145 MHz") for c in "ABC" for line in lines))
        self.assertIn("Belge sınıfı belirtilmedi", lines[-1])


class FailClosedTests(unittest.TestCase):
    def test_off_topic_question_is_not_answered(self):
        result = ask.answer("Bugün hava nasıl olacak?", KB)
        self.assertTrue(result["fail_closed"])
        self.assertIn("cevaplayamıyorum", ask.render(result))

    def test_pending_topic_refuses_legal_verdict(self):
        result = ask.answer("Çağrı işareti nasıl alırım?", KB)
        self.assertFalse(result["fail_closed"])
        self.assertEqual(result["legal_basis"], [])
        self.assertTrue(any("henüz doğrulanmadı" in line for line in result["short_answer"]))

    def test_all_cited_rules_are_verified_on_verified_sources(self):
        for question, _ in DIRECTIVE_QUESTIONS:
            result = ask.answer(question, KB)
            for item in result["legal_basis"] + result["amateur_practice"]:
                with self.subTest(rule=item["rule_id"]):
                    self.assertIsNotNone(KB.usable_rule(item["rule_id"]))
            for item in result["legal_basis"]:
                source = KB.sources[item["source_id"]]
                self.assertEqual((source["source_type"], source["legal_status"]), ("official_legal", "current"))

    def test_unverified_rule_is_never_cited(self):
        kb = ask.Knowledge()
        kb.rules = copy.deepcopy(kb.rules)
        kb.rules["TR.AMATEUR.NO_OBSCURING_ENCRYPTION"]["verification_status"] = "pending"
        result = ask.answer("Şifreli haberleşme yapabilir miyim?", kb)
        self.assertTrue(result["fail_closed"])


class SelfCheckTests(unittest.TestCase):
    def check(self, mutate):
        kb = ask.Knowledge()
        kb.intents = copy.deepcopy(kb.intents)
        mutate(kb.intents)
        return ask.self_check(kb)

    def test_repository_intents_are_valid(self):
        self.assertEqual(ask.self_check(KB), [])

    def test_unknown_rule_rejected(self):
        self.assertTrue(self.check(lambda i: i[0]["legal_rule_ids"].append("TR.AMATEUR.NOPE")))

    def test_practice_rule_cannot_be_legal(self):
        self.assertTrue(self.check(lambda i: i[0]["legal_rule_ids"].append("IARU.R1.NATIONAL_RULES_PREVAIL")))

    def test_verified_source_cannot_be_listed_as_pending(self):
        self.assertTrue(self.check(lambda i: i[0]["pending_source_ids"].append("TR.KEGM.AMATEUR.FAQ")))

    def test_pending_source_cannot_be_reference(self):
        self.assertTrue(self.check(lambda i: i[0]["reference_source_ids"].append("TR.BTK.EHK.5809")))

    def test_duplicate_keyword_across_intents_rejected(self):
        self.assertTrue(self.check(lambda i: i[1]["keywords"].append(i[0]["keywords"][0])))

    def test_empty_intent_rejected(self):
        def empty(intents):
            for key in ("legal_rule_ids", "practice_rule_ids", "reference_source_ids", "pending_source_ids"):
                intents[0][key] = []
        self.assertTrue(self.check(empty))


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "ask.py"), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def test_json_bundle(self):
        payload = json.loads(self.run_cli("--json", "Dummy load ne zaman zorunlu?"))
        self.assertEqual(payload["legal_basis"][0]["rule_id"], "TR.AMATEUR.DUMMY_LOAD")

    def test_text_sections(self):
        out = self.run_cli("C sınıfı belgeyle 145 MHz'te kaç watt kullanabilirim?")
        for heading in ("Kısa cevap:", "Resmî / hukuki dayanak:", "Teknik sınırlar:",
                        "Amatör uygulama / IARU / TRAC tavsiyesi", "Kaynaklar:"):
            self.assertIn(heading, out)

    def test_readme_example_matches_engine_output(self):
        readme = (ROOT / "README.md").read_text("utf-8")
        line = ask.answer("C sınıfı belgeyle 145 MHz'te 10 W kullanabilir miyim?", KB)["short_answer"][0]
        self.assertIn(f"- {line}", readme)

    def test_self_check_cli(self):
        self.assertIn("PASS", self.run_cli("--self-check"))


if __name__ == "__main__":
    unittest.main()
