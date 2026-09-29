import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "qso_log_adif", ROOT / "scripts" / "qso_log_adif.py"
)
qso = importlib.util.module_from_spec(spec)
sys.modules["qso_log_adif"] = qso
assert spec.loader is not None
spec.loader.exec_module(qso)

CONTRACT = json.loads((ROOT / "data" / "qso_log_contract.json").read_text("utf-8"))

BASE = {
    "CALL": "TA1ABC",
    "QSO_DATE": "20260929",
    "TIME_ON": "001530",
    "BAND": "2m",
    "MODE": "FM",
}


class QsoValidationTests(unittest.TestCase):
    def test_valid_band_record(self):
        self.assertEqual(qso.validate_record(BASE, CONTRACT), BASE)

    def test_valid_frequency_only_record(self):
        record = dict(BASE)
        del record["BAND"]
        record["FREQ"] = "145.500"
        self.assertEqual(qso.validate_record(record, CONTRACT)["FREQ"], "145.500")

    def test_band_or_freq_is_required(self):
        record = dict(BASE)
        del record["BAND"]
        with self.assertRaises(ValueError):
            qso.validate_record(record, CONTRACT)

    def test_required_field_is_enforced(self):
        record = dict(BASE)
        del record["CALL"]
        with self.assertRaises(ValueError):
            qso.validate_record(record, CONTRACT)

    def test_unknown_field_is_rejected(self):
        record = dict(BASE)
        record["LEGAL_TO_TRANSMIT"] = "YES"
        with self.assertRaises(ValueError):
            qso.validate_record(record, CONTRACT)

    def test_invalid_calendar_date_rejected(self):
        record = dict(BASE)
        record["QSO_DATE"] = "20260230"
        with self.assertRaises(ValueError):
            qso.validate_record(record, CONTRACT)

    def test_invalid_time_rejected(self):
        for value in ("2400", "126099", "12:30"):
            with self.subTest(value=value):
                record = dict(BASE)
                record["TIME_ON"] = value
                with self.assertRaises(ValueError):
                    qso.validate_record(record, CONTRACT)

    def test_nonpositive_or_invalid_frequency_rejected(self):
        for value in ("0", "-1", "NaN", "abc"):
            with self.subTest(value=value):
                record = dict(BASE)
                record["FREQ"] = value
                with self.assertRaises(ValueError):
                    qso.validate_record(record, CONTRACT)

    def test_non_ascii_or_newline_rejected(self):
        for field, value in (("COMMENT", "çağrı"), ("COMMENT", "line1\nline2")):
            with self.subTest(value=value):
                record = dict(BASE)
                record[field] = value
                with self.assertRaises(ValueError):
                    qso.validate_record(record, CONTRACT)


class AdiExportTests(unittest.TestCase):
    def test_data_specifier_uses_exact_length(self):
        self.assertEqual(qso.adi_data_specifier("CALL", "TA1ABC"), "<CALL:6>TA1ABC")

    def test_record_order_and_eor(self):
        exported = qso.export_record(BASE, CONTRACT)
        self.assertTrue(exported.startswith("<QSO_DATE:8>20260929<TIME_ON:6>001530<CALL:6>TA1ABC"))
        self.assertIn("<BAND:2>2m", exported)
        self.assertIn("<MODE:2>FM", exported)
        self.assertTrue(exported.endswith("<EOR>"))

    def test_log_header_uses_current_adif_version(self):
        exported = qso.export_log([BASE], contract=CONTRACT)
        self.assertTrue(exported.startswith("<ADIF_VER:5>3.1.7<PROGRAMID:6>TELSIZ<EOH>"))

    def test_multiple_records_each_have_eor(self):
        exported = qso.export_log([BASE, BASE], contract=CONTRACT)
        self.assertEqual(exported.count("<EOR>"), 2)

    def test_empty_log_rejected(self):
        with self.assertRaises(ValueError):
            qso.export_log([], contract=CONTRACT)

    def test_invalid_program_id_rejected(self):
        with self.assertRaises(ValueError):
            qso.export_log([BASE], program_id="TEL\nSIZ", contract=CONTRACT)

    def test_export_never_invents_legal_permission_field(self):
        exported = qso.export_log([BASE], contract=CONTRACT)
        self.assertNotIn("LEGAL", exported.upper())


class AdiParseTests(unittest.TestCase):
    def test_round_trip_with_exporter(self):
        text = qso.export_log([BASE, dict(BASE, CALL="TA2XYZ")], contract=CONTRACT)
        parsed = qso.parse_adi(text)
        self.assertEqual(parsed["header"], {"ADIF_VER": CONTRACT["adif_version"], "PROGRAMID": "TELSIZ"})
        self.assertEqual(parsed["records"], [BASE, dict(BASE, CALL="TA2XYZ")])

    def test_type_indicator_and_case(self):
        parsed = qso.parse_adi("<call:6>TA1ABC<qso_date:8:d>20260929<eor>")
        self.assertEqual(parsed["records"], [{"CALL": "TA1ABC", "QSO_DATE": "20260929"}])

    def test_length_governs_value(self):
        parsed = qso.parse_adi("<COMMENT:3>a<b<EOR>")
        self.assertEqual(parsed["records"][0]["COMMENT"], "a<b")

    def test_malformed_input_rejected(self):
        for bad in ("<CALL:9>TA1<EOR>", "<CALL:3>TA1", "no tags", "<CALL>TA1<EOR>"):
            with self.assertRaises(ValueError):
                qso.parse_adi(bad)


class AdifAnswerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec_ask = importlib.util.spec_from_file_location("ask", ROOT / "scripts" / "ask.py")
        if "ask" not in sys.modules:
            module = importlib.util.module_from_spec(spec_ask)
            sys.modules["ask"] = module
            spec_ask.loader.exec_module(module)
        cls.ask = sys.modules["ask"]
        cls.kb = cls.ask.Knowledge()

    def routes(self, question):
        result = self.ask.answer(question, self.kb)
        return result, {t["topic"]: t for t in result["technical_knowledge"]}

    def test_contract_summary(self):
        result, routes = self.routes("ADIF kaydında hangi alanlar zorunlu?")
        summary = " ".join(routes["QSO kaydı / ADIF"]["summary"])
        self.assertIn("CALL, QSO_DATE, TIME_ON, MODE", summary)
        self.assertEqual(routes["QSO kaydı / ADIF"]["source_ids"], ["ADIF.SPEC.3.1.7"])
        self.assertEqual(result["legal_basis"], [])

    def test_record_checked_and_limits_disclosed(self):
        _, routes = self.routes(
            "ADIF <CALL:6>TA1ABC<QSO_DATE:8>20260929<TIME_ON:4>1530<MODE:2>FM<BAND:2>2m<EOR>")
        summary = " ".join(routes["QSO kaydı / ADIF"]["summary"])
        self.assertIn("sözleşmesine uygun", summary)
        self.assertIn("BAND/MODE değer listeleri denetlenmedi", summary)
        self.assertEqual([t for t in routes if t.startswith("Q kod")], [])

    def test_invalid_record_reported(self):
        _, routes = self.routes("ADIF <CALL:6>TA1ABC<QSO_DATE:8>20261399<TIME_ON:4>1530<MODE:2>FM<BAND:2>2m<EOR>")
        self.assertIn("uymuyor", " ".join(routes["QSO kaydı / ADIF"]["summary"]))


if __name__ == "__main__":
    unittest.main()
