import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vk = load_module("validate_knowledge")
fl = load_module("frequency_lookup")

SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}
RULES = {r["id"]: r for r in json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))["rules"]}
TABLE = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))
RAW = json.loads((ROOT / "data" / "btk_amateur_table_raw.json").read_text("utf-8"))
LEGAL_SOURCE = "TR.BTK.FTM.TECH.2022-IK-SYD-245"
FAKE_SHA = "a" * 64


def full_row(**overrides):
    """A fully extracted synthetic row (test fixture only, not real data)."""
    row = {
        "id": "TR.TEST.ROW.A.1",
        "frequency_min": 10,
        "frequency_max": 20,
        "unit": "MHz",
        "license_class": ["A"],
        "maximum_output_power": 100,
        "power_unit": "W",
        "emission": ["F3E"],
        "bandwidth": "12.5 kHz",
        "station_type": ["fixed"],
        "allowed_use": ["simplex"],
        "prohibited_use": [],
        "special_conditions": [],
        "allocation_status": "primary",
        "satellite": False,
        "repeater": False,
        "beacon": False,
        "emergency": False,
        "footnotes": [],
        "source_id": LEGAL_SOURCE,
        "source_locator": {"table": "test"},
        "verification_status": "verified",
    }
    row.update(overrides)
    return row


def complete_table(rows):
    return {
        "schema_version": 1,
        "source_id": LEGAL_SOURCE,
        "coverage_status": "complete",
        "coverage_blocker": None,
        "artifact": {
            "source_url": "https://example.invalid/test.pdf",
            "fetched_at": "2026-09-28T00:00:00Z",
            "http_status": 200,
            "content_type": "application/pdf",
            "file_size": 1,
            "sha256": FAKE_SHA,
            "pdf_page_count": 1,
        },
        "row_count_reconciliation": {
            "table_start_locator": "start",
            "table_end_locator": "end",
            "source_rows_counted": len(rows),
            "footnotes_counted": 0,
            "footnotes_recorded": 0,
        },
        "rows": rows,
    }


def hashed_sources():
    sources = copy.deepcopy(SOURCES)
    sources[LEGAL_SOURCE]["content_sha256"] = FAKE_SHA
    return sources


def request(**kwargs):
    return fl.Request(**kwargs)


class FrequencyTableValidationTests(unittest.TestCase):
    def validate(self, table, sources=None):
        vk.validate_frequency_table(table, sources or SOURCES, RULES)

    def test_repository_table_is_valid(self):
        self.validate(TABLE)

    def test_partial_coverage_requires_blocker(self):
        table = copy.deepcopy(TABLE)
        table["coverage_blocker"] = None
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_complete_coverage_rejected_without_source_hash(self):
        table = complete_table([full_row()])
        sources = copy.deepcopy(SOURCES)
        sources[LEGAL_SOURCE]["content_sha256"] = None
        with self.assertRaises(SystemExit):
            self.validate(table, sources)

    def test_complete_coverage_accepts_fully_evidenced_table(self):
        self.validate(complete_table([full_row()]), hashed_sources())

    def test_complete_coverage_rejects_artifact_hash_mismatch(self):
        table = complete_table([full_row()])
        table["artifact"]["sha256"] = "b" * 64
        with self.assertRaises(SystemExit):
            self.validate(table, hashed_sources())

    def test_complete_coverage_rejects_missing_artifact(self):
        table = complete_table([full_row()])
        table["artifact"] = None
        with self.assertRaises(SystemExit):
            self.validate(table, hashed_sources())

    def test_complete_coverage_rejects_row_count_mismatch(self):
        table = complete_table([full_row()])
        table["row_count_reconciliation"]["source_rows_counted"] = 2
        with self.assertRaises(SystemExit):
            self.validate(table, hashed_sources())

    def test_complete_coverage_rejects_unrecorded_footnotes(self):
        table = complete_table([full_row()])
        table["row_count_reconciliation"]["footnotes_counted"] = 3
        with self.assertRaises(SystemExit):
            self.validate(table, hashed_sources())

    def test_complete_coverage_rejects_unextracted_fields(self):
        with self.assertRaises(SystemExit):
            self.validate(complete_table([full_row(emission=None)]), hashed_sources())

    def test_repository_table_cannot_be_flipped_to_complete(self):
        table = copy.deepcopy(TABLE)
        table["coverage_status"] = "complete"
        table["coverage_blocker"] = None
        with self.assertRaises(SystemExit):
            self.validate(table, SOURCES)

    def test_repository_partial_table_uses_bound_artifact_hash(self):
        self.assertEqual(TABLE["artifact"]["sha256"], SOURCES[LEGAL_SOURCE]["content_sha256"])
        self.assertEqual(TABLE["artifact"]["file_size"], 508766)
        self.assertEqual(TABLE["artifact"]["http_status"], 200)

    # integrity
    def test_row_source_must_exist(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["source_id"] = "TR.DOES.NOT.EXIST"
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_verified_row_rejects_pending_source(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["source_id"] = "TR.BTK.EHK.5809"
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_verified_row_rejects_noncurrent_source(self):
        sources = copy.deepcopy(SOURCES)
        sources[LEGAL_SOURCE]["legal_status"] = "superseded"
        with self.assertRaises(SystemExit):
            self.validate(TABLE, sources)

    def test_row_requires_source_locator(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["source_locator"] = {}
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_duplicate_row_id_rejected(self):
        table = copy.deepcopy(TABLE)
        table["rows"].append(copy.deepcopy(table["rows"][0]))
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_conflicting_overlapping_rows_rejected(self):
        table = copy.deepcopy(TABLE)
        clone = copy.deepcopy(table["rows"][0])
        clone.update(id="TR.FTM.AMATEUR.ROW.C.CLONE", maximum_output_power=50, derived_from_rule=None)
        table["rows"].append(clone)
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_invalid_range_rejected(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0].update(frequency_min=146, frequency_max=144, derived_from_rule=None)
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_negative_power_rejected(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0].update(maximum_output_power=-5, derived_from_rule=None)
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_row_must_agree_with_source_rule(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["maximum_output_power"] = 50
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_row_cannot_extend_beyond_rule_scope(self):
        table = copy.deepcopy(TABLE)
        table["rows"][1].update(frequency_min=429.0)
        with self.assertRaises(SystemExit):
            self.validate(table)

    # raw cross-check
    def test_repository_rows_lie_inside_raw_rows(self):
        vk.validate_rows_within_raw(TABLE, RAW)

    def test_row_spanning_subband_gap_rejected(self):
        table = copy.deepcopy(TABLE)
        table["rows"][1].update(frequency_min=430, frequency_max=440)
        with self.assertRaises(SystemExit):
            vk.validate_rows_within_raw(table, RAW)

    def test_row_class_not_listed_in_raw_rejected(self):
        table = copy.deepcopy(TABLE)
        table["rows"].append(full_row(id="TR.TEST.ROW.C.50", frequency_min=50, frequency_max=52, license_class=["C"]))
        with self.assertRaises(SystemExit):
            vk.validate_rows_within_raw(table, RAW)

    def test_raw_cross_check_rejects_source_mismatch(self):
        raw = copy.deepcopy(RAW)
        raw["source_id"] = "TR.OTHER"
        with self.assertRaises(SystemExit):
            vk.validate_rows_within_raw(TABLE, raw)

    # authority
    def test_iaru_row_cannot_be_verified_legal_row(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0].update(source_id="IARU.R1.BANDPLANS", derived_from_rule=None)
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_trac_row_cannot_be_verified_legal_row(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0].update(source_id="TR.TRAC.TECHNICAL.PROJECTS", derived_from_rule=None)
        with self.assertRaises(SystemExit):
            self.validate(table)


class EvaluateContractTests(unittest.TestCase):
    def evaluate(self, table=TABLE, sources=SOURCES, **kwargs):
        return fl.evaluate(table, sources, request(**kwargs))

    # positive known
    def test_c_145_mhz_finds_known_row_and_limit(self):
        result = self.evaluate(license_class="C", frequency_mhz=145.0)
        self.assertEqual(result["rows"], ["TR.FTM.AMATEUR.ROW.C.144-146"])
        self.assertEqual(result["known_limits"][0]["max_output_power"], 5)

    def test_c_433_5_mhz_finds_known_subband_row_and_limit(self):
        result = self.evaluate(license_class="C", frequency_mhz=433.5)
        self.assertEqual(result["rows"], ["TR.FTM.AMATEUR.ROW.C.433.4-433.575"])
        self.assertEqual(result["known_limits"][0]["max_output_power"], 5)
        self.assertEqual(result["known_limits"][0]["power_unit"], "W")

    def test_c_repeater_subband_is_its_own_row(self):
        result = self.evaluate(license_class="C", frequency_mhz=431.6)
        self.assertEqual(result["rows"], ["TR.FTM.AMATEUR.ROW.C.431.55-431.825"])

    def test_a_51_mhz_finds_verified_general_100w_limit(self):
        result = self.evaluate(license_class="A", frequency_mhz=51.0)
        self.assertEqual(result["rows"], ["TR.FTM.AMATEUR.ROW.AB.50-52"])
        self.assertEqual(result["known_limits"][0]["max_output_power"], 100)

    def test_b_51_mhz_finds_verified_general_100w_limit(self):
        result = self.evaluate(license_class="B", frequency_mhz=51.0)
        self.assertEqual(result["rows"], ["TR.FTM.AMATEUR.ROW.AB.50-52"])
        self.assertEqual(result["known_limits"][0]["max_output_power"], 100)

    def test_c_51_mhz_is_not_inferred_from_ab_row(self):
        result = self.evaluate(license_class="C", frequency_mhz=51.0)
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_gaps_between_430_440_subbands_have_no_row(self):
        for freq in (430.0, 431.0, 433.0, 434.0, 438.5, 439.9):
            with self.subTest(freq=freq):
                result = self.evaluate(license_class="C", frequency_mhz=freq, requested_power_w=5)
                self.assertEqual(result["rows"], [])
                self.assertEqual(result["known_limits"], [])
                self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_frequency_doc_lists_exactly_the_semantic_rows(self):
        import re

        doc = (ROOT / "docs" / "FREQUENCY_TABLE.md").read_text("utf-8")
        documented = set(re.findall(r"`(TR\.FTM\.AMATEUR\.ROW\.[^`]+)`", doc))
        self.assertEqual(documented, {row["id"] for row in TABLE["rows"]})

    def test_430_group_rows_match_raw_subbands_exactly(self):
        raw = json.loads((ROOT / "data" / "btk_amateur_table_raw.json").read_text("utf-8"))
        raw_430 = sorted(
            (r["frequency_min"], r["frequency_max"])
            for r in raw["rows"]
            if r["unit"] == "MHz" and 430 <= r["frequency_min"] < 440
        )
        semantic_430 = sorted(
            (r["frequency_min"], r["frequency_max"])
            for r in TABLE["rows"]
            if r["unit"] == "MHz" and 430 <= r["frequency_min"] < 440
        )
        self.assertEqual(semantic_430, raw_430)

    # fail closed
    def test_unknown_frequency_is_unknown_not_forbidden(self):
        result = self.evaluate(license_class="A", frequency_mhz=14.2, requested_power_w=100)
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_missing_license_class_is_unknown(self):
        result = self.evaluate(frequency_mhz=145.0)
        self.assertEqual(result["legal_status"], fl.UNKNOWN)
        self.assertIn("input:license_class", result["missing"])

    def test_missing_frequency_is_unknown(self):
        result = self.evaluate(license_class="C")
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_other_jurisdiction_is_unknown(self):
        result = self.evaluate(jurisdiction="DE", license_class="C", frequency_mhz=145.0)
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_partial_table_gives_no_blanket_verdict_even_with_all_inputs(self):
        result = self.evaluate(
            license_class="C", frequency_mhz=145.0, requested_power_w=5, emission="F3E",
            bandwidth="12.5 kHz", station_type="portable", context="simplex",
        )
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_missing_emission_does_not_fabricate_permission(self):
        result = self.evaluate(license_class="C", frequency_mhz=145.0, requested_power_w=5)
        self.assertEqual(result["legal_status"], fl.UNKNOWN)
        self.assertIn("row:emission", result["missing"])
        self.assertIn("input:emission", result["missing"])

    def test_missing_power_does_not_fabricate_power(self):
        result = self.evaluate(license_class="C", frequency_mhz=145.0, emission="F3E")
        self.assertEqual(result["legal_status"], fl.UNKNOWN)
        self.assertIn("input:requested_power_w", result["missing"])

    def test_b_class_not_inferred_from_c_rows(self):
        result = self.evaluate(license_class="B", frequency_mhz=145.0)
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_power_above_verified_limit_is_not_allowed(self):
        result = self.evaluate(license_class="C", frequency_mhz=433.5, requested_power_w=10)
        self.assertEqual(result["legal_status"], fl.NOT_ALLOWED)

    def test_power_within_limit_is_still_unknown_on_partial_table(self):
        result = self.evaluate(license_class="C", frequency_mhz=433.5, requested_power_w=5)
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_ab_51_mhz_power_above_verified_general_limit_is_not_allowed(self):
        for license_class in ("A", "B"):
            with self.subTest(license_class=license_class):
                result = self.evaluate(
                    license_class=license_class,
                    frequency_mhz=51.0,
                    requested_power_w=101,
                )
                self.assertEqual(result["legal_status"], fl.NOT_ALLOWED)

    def test_ab_51_mhz_within_general_limit_remains_unknown(self):
        result = self.evaluate(
            license_class="A",
            frequency_mhz=51.0,
            requested_power_w=100,
        )
        self.assertEqual(result["legal_status"], fl.UNKNOWN)
        self.assertIn("row:emission", result["missing"])

    def test_51_mhz_beacon_context_remains_unknown_until_special_25w_limit_is_modeled(self):
        result = self.evaluate(
            license_class="A",
            frequency_mhz=51.0,
            requested_power_w=50,
            context="beacon",
        )
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    # authority at evaluation time
    def test_iaru_row_cannot_create_permission(self):
        table = complete_table([full_row(source_id="IARU.R1.BANDPLANS")])
        result = self.evaluate(table, hashed_sources(), license_class="A", frequency_mhz=15,
                               requested_power_w=10, emission="F3E", bandwidth="12.5 kHz",
                               station_type="fixed", context="simplex")
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_trac_row_cannot_create_permission(self):
        table = complete_table([full_row(source_id="TR.TRAC.TECHNICAL.PROJECTS")])
        result = self.evaluate(table, hashed_sources(), license_class="A", frequency_mhz=15,
                               requested_power_w=10, emission="F3E", bandwidth="12.5 kHz",
                               station_type="fixed", context="simplex")
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_pending_official_source_cannot_create_permission(self):
        table = complete_table([full_row(source_id="TR.BTK.EHK.5809")])
        result = self.evaluate(table, hashed_sources(), license_class="A", frequency_mhz=15,
                               requested_power_w=10, emission="F3E", bandwidth="12.5 kHz",
                               station_type="fixed", context="simplex")
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    # verdict paths on a synthetic complete table
    def full_request(self, **overrides):
        values = dict(license_class="A", frequency_mhz=15, requested_power_w=10, emission="F3E",
                      bandwidth="12.5 kHz", station_type="fixed", context="simplex")
        values.update(overrides)
        return values

    def test_complete_fully_matched_row_is_allowed(self):
        table = complete_table([full_row()])
        result = self.evaluate(table, hashed_sources(), **self.full_request())
        self.assertEqual(result["legal_status"], fl.ALLOWED)

    def test_row_conditions_yield_allowed_with_conditions(self):
        table = complete_table([full_row(footnotes=["dipnot 1"])])
        result = self.evaluate(table, hashed_sources(), **self.full_request())
        self.assertEqual(result["legal_status"], fl.ALLOWED_WITH_CONDITIONS)
        self.assertEqual(result["unacknowledged_conditions"], ["dipnot 1"])

    def test_unlisted_emission_on_complete_table_is_not_allowed(self):
        table = complete_table([full_row()])
        result = self.evaluate(table, hashed_sources(), **self.full_request(emission="J3E"))
        self.assertEqual(result["legal_status"], fl.NOT_ALLOWED)

    def test_explicitly_prohibited_context_is_not_allowed(self):
        table = complete_table([full_row(prohibited_use=["repeater"])])
        result = self.evaluate(table, hashed_sources(), **self.full_request(context="repeater"))
        self.assertEqual(result["legal_status"], fl.NOT_ALLOWED)

    def test_unconfirmed_bandwidth_is_unknown(self):
        table = complete_table([full_row()])
        result = self.evaluate(table, hashed_sources(), **self.full_request(bandwidth="25 kHz"))
        self.assertEqual(result["legal_status"], fl.UNKNOWN)

    def test_missing_row_on_complete_table_is_unknown(self):
        table = complete_table([full_row()])
        result = self.evaluate(table, hashed_sources(), **self.full_request(frequency_mhz=50))
        self.assertEqual(result["legal_status"], fl.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
