import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ask", ROOT / "scripts" / "ask.py")
ask = sys.modules.get("ask") or importlib.util.module_from_spec(spec)
if "ask" not in sys.modules:
    sys.modules["ask"] = ask
    assert spec.loader is not None
    spec.loader.exec_module(ask)

KB = ask.Knowledge()


def run(question):
    return ask.answer(question, KB)


def summary(result):
    return " ".join(result["short_answer"])


def topics(result):
    return {t["topic"] for t in result["technical_knowledge"]}


class QCodeTests(unittest.TestCase):
    def test_every_registered_q_code_is_answerable(self):
        codes = [c["code"] for c in json.loads((ROOT / "data" / "q_codes.json").read_text("utf-8"))["codes"]]
        for code in codes:
            with self.subTest(code=code):
                result = run(f"{code} ne demek?")
                self.assertIn(f"{code} — soru biçimi", summary(result))
                self.assertIn("IARU.R1.EOP.4.2.0", {s["source_id"] for s in result["sources"]})

    def test_unknown_q_code_is_not_invented(self):
        result = run("QZZ ne demek?")
        self.assertEqual(result["technical_knowledge"], [])
        self.assertTrue(result["fail_closed"])


class RstTests(unittest.TestCase):
    def test_phone_report(self):
        text = summary(run("Karşı istasyon 59 rapor verdi"))
        self.assertIn("59 raporu, ses (RS, 2 hane): R=5", text)
        self.assertIn("S=9", text)

    def test_cw_report_has_tone(self):
        self.assertIn("T=9", summary(run("CW'de RST 599 ne demek?")))

    def test_out_of_scale_report_is_ignored_not_invented(self):
        result = run("RS 50 raporu ne demek?")
        self.assertEqual(topics(result), set())

    def test_digits_without_report_keyword_are_ignored(self):
        self.assertNotIn("RS(T) raporu", topics(run("145 MHz'te kaç watt?")))


class MorseTests(unittest.TestCase):
    def test_encode_quoted_text(self):
        self.assertIn("-.-. --.- / - . ... -", summary(run('Mors "CQ TEST" nasıl yazılır?')))

    def test_decode_signal(self):
        self.assertIn("çözümü: SOS", summary(run("Mors ... --- ... ne demek?")))

    def test_ellipsis_is_not_decoded(self):
        text = summary(run("Mors öğrenmek istiyorum..."))
        self.assertNotIn("çözümü", text)
        self.assertIn("tırnak içinde", text)

    def test_source_is_itu(self):
        result = run('Mors "SOS"')
        self.assertIn("ITU.R.M1677.1", {s["source_id"] for s in result["sources"]})


class WavelengthTests(unittest.TestCase):
    def test_quarter_wave_145(self):
        result = run("145 MHz için çeyrek dalga anten boyu kaç?")
        self.assertIn("λ/4 = 0,517 m", summary(result))
        self.assertEqual(result["legal_basis"], [])
        self.assertIn("BIPM.SI.DEFINING_CONSTANTS", {s["source_id"] for s in result["sources"]})

    def test_velocity_factor(self):
        self.assertIn("hız faktörü 0,95", summary(run("7,1 MHz dipol anten uzunluğu hız faktörü 0,95")))

    def test_wavelength_with_class_keeps_legal_answer(self):
        result = run("C sınıfı 145 MHz çeyrek dalga anten boyu")
        self.assertIn("λ/4", summary(result))
        self.assertIn("C sınıfı, 145 MHz", summary(result))

    def test_assumptions_are_disclosed(self):
        details = run("145 MHz dalga boyu")["technical_knowledge"][0]["details"]
        self.assertTrue(any(line.startswith("varsayım") for line in details))


class RepeaterTests(unittest.TestCase):
    def test_known_branch_lists_repeaters_with_disclaimer(self):
        result = run("Ankara röleleri hangileri?")
        self.assertIn("ANKARA / ", summary(result))
        details = " ".join(t for item in result["technical_knowledge"] for t in item["details"])
        self.assertIn("BTK izni yerine geçmez", details)
        self.assertIn("TR.AMATEUR.REPEATER_AND_EXPERIMENTAL", {i["rule_id"] for i in result["legal_basis"]})

    def test_unknown_city_does_not_invent_repeaters(self):
        result = run("Erzurum röleleri hangileri?")
        self.assertNotIn("Röle listesi (dernek bilgisi)", topics(result))


class GridTests(unittest.TestCase):
    def test_locator_bounds(self):
        self.assertIn("KN41: merkez yaklaşık 41,5000°, 29,0000°", summary(run("KN41 locator nerede?")))

    def test_coordinates_to_locator(self):
        self.assertIn("KN41ma", summary(run("41.0, 29.0 koordinatının grid locator'ı nedir?")))

    def test_grid_is_marked_educational(self):
        details = run("KN41 locator")["technical_knowledge"][0]["details"]
        self.assertIn("ACADEMY.TOOL.GRID-LOCATOR", details[0])


class BoundaryTests(unittest.TestCase):
    def test_technical_answers_never_add_legal_basis_by_themselves(self):
        for question in ("QTH ne demek?", "RST 599", 'Mors "SOS"', "145 MHz dalga boyu", "KN41 locator"):
            with self.subTest(question=question):
                result = run(question)
                self.assertEqual(result["legal_basis"], [])
                self.assertFalse(result["fail_closed"])

    def test_off_topic_still_fails_closed(self):
        self.assertTrue(run("Bugün hava nasıl olacak?")["fail_closed"])

    def test_only_verified_sources_are_listed(self):
        for question in ("QTH ne demek?", "Ankara röleleri", "145 MHz dalga boyu"):
            for source in run(question)["sources"]:
                with self.subTest(question=question, source=source["source_id"]):
                    self.assertEqual(source["verification_status"], "verified")


if __name__ == "__main__":
    unittest.main()
