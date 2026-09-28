import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grid_locator", ROOT / "scripts" / "grid_locator.py")
grid = importlib.util.module_from_spec(spec)
sys.modules["grid_locator"] = grid
assert spec.loader is not None
spec.loader.exec_module(grid)


class MaidenheadEncodeTests(unittest.TestCase):
    def test_null_island_known_locator(self):
        self.assertEqual(grid.maidenhead_encode(0.0, 0.0), "JJ00aa")

    def test_global_lower_bound(self):
        self.assertEqual(grid.maidenhead_encode(-90.0, -180.0), "AA00aa")

    def test_precision_2(self):
        self.assertEqual(grid.maidenhead_encode(0.0, 0.0, 2), "JJ")

    def test_precision_4(self):
        self.assertEqual(grid.maidenhead_encode(0.0, 0.0, 4), "JJ00")

    def test_precision_6_uses_lowercase_subsquare(self):
        value = grid.maidenhead_encode(41.0082, 28.9784, 6)
        self.assertRegex(value, r"^[A-R]{2}[0-9]{2}[a-x]{2}$")

    def test_upper_latitude_bound_rejected(self):
        with self.assertRaises(ValueError):
            grid.maidenhead_encode(90.0, 0.0)

    def test_upper_longitude_bound_rejected(self):
        with self.assertRaises(ValueError):
            grid.maidenhead_encode(0.0, 180.0)

    def test_below_lower_bounds_rejected(self):
        with self.assertRaises(ValueError):
            grid.maidenhead_encode(-90.0001, 0.0)
        with self.assertRaises(ValueError):
            grid.maidenhead_encode(0.0, -180.0001)

    def test_non_finite_values_rejected(self):
        for value in (math.inf, -math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    grid.maidenhead_encode(value, 0.0)

    def test_boolean_is_not_accepted_as_coordinate(self):
        with self.assertRaises(ValueError):
            grid.maidenhead_encode(True, 0.0)

    def test_invalid_precision_rejected(self):
        with self.assertRaises(ValueError):
            grid.maidenhead_encode(0.0, 0.0, 8)


class MaidenheadBoundsTests(unittest.TestCase):
    def test_null_island_bounds(self):
        bounds = grid.maidenhead_bounds("JJ00aa")
        self.assertEqual(bounds["locator"], "JJ00aa")
        self.assertAlmostEqual(bounds["longitude_min"], 0.0)
        self.assertAlmostEqual(bounds["latitude_min"], 0.0)
        self.assertAlmostEqual(bounds["longitude_max"], 1.0 / 12.0)
        self.assertAlmostEqual(bounds["latitude_max"], 1.0 / 24.0)

    def test_locator_is_case_normalized(self):
        self.assertEqual(grid.maidenhead_bounds("jj00AA")["locator"], "JJ00aa")

    def test_encode_coordinate_lies_inside_decoded_cell(self):
        lat, lon = 41.0082, 28.9784
        locator = grid.maidenhead_encode(lat, lon)
        bounds = grid.maidenhead_bounds(locator)
        self.assertLessEqual(bounds["latitude_min"], lat)
        self.assertLess(lat, bounds["latitude_max"])
        self.assertLessEqual(bounds["longitude_min"], lon)
        self.assertLess(lon, bounds["longitude_max"])

    def test_roundtrip_center_reencodes_same_locator(self):
        for locator in ("JJ00aa", "FN30ar", "KN41la", "AA00aa"):
            with self.subTest(locator=locator):
                bounds = grid.maidenhead_bounds(locator)
                self.assertEqual(
                    grid.maidenhead_encode(
                        bounds["center_latitude"],
                        bounds["center_longitude"],
                    ),
                    locator,
                )

    def test_invalid_locator_rejected(self):
        for locator in ("", "J", "SS00aa", "JJ0", "JJ00zz", "JJ00aa00", 123):
            with self.subTest(locator=locator):
                with self.assertRaises(ValueError):
                    grid.maidenhead_bounds(locator)


if __name__ == "__main__":
    unittest.main()
