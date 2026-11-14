"""Offline checks for the dose-response lab (Part 4)

Each test states one assumption of the lesson or one failure case and proves the code handles it.
No network and no saved outputs are needed; the tests only read data/raw/ (the Part 3 manifest).

HOW TO RUN IT
  python -m unittest discover -s code -p "test_dose_response_lab.py" -v
"""

# unittest runs the checks; copy makes safe edited copies of the manifest for the failure tests.
import copy
import json
from pathlib import Path
import unittest

# NumPy comparison helpers for arrays.
import numpy as np

# The functions under test live in dose_response_lab.py (same code/ folder).
from dose_response_lab import (
    DOSES_NM, ROOT, absolute_crossing, fit_hill, hill, normalize,
    pic50, synthetic_data, validate_prerequisite,
)


class DoseResponseTests(unittest.TestCase):
    """Checks of normalization, units, fitting, refusal rules and the Part 3 identity check."""
    def test_normalization_and_no_hidden_clipping(self):
        """Vehicle = 0 percent, inhibited reference = 100 percent, and out-of-range values are kept, not clipped."""
        np.testing.assert_allclose(normalize([1000, 550, 100, 1010, 90], 1000, 100),
                                   [0, 50, 100, -100 / 90, 100 + 100 / 90])
        with self.assertRaises(ValueError):
            normalize([1], 100, 100)

    def test_unit_conversion_requires_molar_scale(self):
        """10 nM is pIC50 8; zero concentrations and non-molar units are refused."""
        self.assertAlmostEqual(pic50(10, "nM"), 8)
        self.assertAlmostEqual(pic50(0.01, "uM"), 8)
        with self.assertRaises(ValueError):
            pic50(0)
        with self.assertRaises(ValueError):
            pic50(5, "mg")

    def test_exact_curve_recovers_midpoint_and_slope(self):
        """A noise-free curve with midpoint 10 nM and slope 1 must be recovered by the fit."""
        result = fit_hill(DOSES_NM, hill(DOSES_NM, 10, 1))
        self.assertEqual(result["status"], "accepted_for_teaching")
        self.assertAlmostEqual(result["absolute_ic50_nm"], 10, places=5)
        self.assertAlmostEqual(result["hill_slope"], 1, places=6)

    def test_fixed_seed_synthetic_wells_are_repeatable(self):
        """The same seed gives identical wells every time (a 9 x 3 array)."""
        first, a = synthetic_data()
        second, b = synthetic_data()
        self.assertEqual(first, second)
        np.testing.assert_array_equal(a, b)
        self.assertEqual(a.shape, (9, 3))

    def test_zero_dose_is_not_silently_logged(self):
        """A zero concentration cannot be put on a log axis, so the fit refuses it."""
        with self.assertRaises(ValueError):
            fit_hill([0, 1, 3, 10, 30], [0, 10, 20, 50, 80])

    def test_unbracketed_curve_refuses_precise_ic50(self):
        """If the data never cross 50 percent, no precise IC50 is reported, only a direction."""
        result = fit_hill(DOSES_NM[:5], hill(DOSES_NM[:5], 1000, 1))
        self.assertEqual(result["status"], "refused")
        self.assertIsNone(result["absolute_ic50_nm"])
        self.assertEqual(result["direction"], "if a monotone 50% crossing exists: > highest tested concentration")

    def test_nonmonotonic_curve_flags_model_failure(self):
        """A curve that goes up, down, up is not one sigmoid, so no IC50 is accepted."""
        result = fit_hill(DOSES_NM, [1, 2, 3, 5, 80, 20, 95, 50, 98])
        self.assertNotEqual(result["status"], "accepted_for_teaching")
        self.assertIsNone(result["absolute_ic50_nm"])

    def test_incomplete_plateau_is_not_absolute_50(self):
        """With a top plateau of 40 percent the relative midpoint exists but absolute 50 percent is never reached."""
        self.assertAlmostEqual(float(hill(10, 10, 1, 0, 40)), 20)
        self.assertIsNone(absolute_crossing(10, 1, 0, 40))
        self.assertEqual(absolute_crossing(100, 1, 10, 70), 200)

    def test_parameter_boundary_is_not_accepted(self):
        """A fit pushed against the search limit is flagged, not accepted."""
        result = fit_hill(DOSES_NM, hill(DOSES_NM, 10, 20))
        self.assertNotEqual(result["status"], "accepted_for_teaching")
        self.assertTrue(any("bound" in reason for reason in result["reasons"]))

    def test_prerequisite_schema_and_exact_chemical_identity(self):
        """A wrong compound ID or a wrong schema version in the Part 3 manifest must raise an error."""
        manifest = json.loads((ROOT / "data/raw/episode03-target_reference_manifest.v1.json").read_text())
        validate_prerequisite(manifest)
        wrong = copy.deepcopy(manifest)
        wrong["reference_compounds"][0]["chembl_id_exact_component_match"] = "CHEMBL4858364"
        with self.assertRaises(ValueError):
            validate_prerequisite(wrong)
        wrong = copy.deepcopy(manifest)
        wrong["schema_version"] = "9"
        with self.assertRaises(ValueError):
            validate_prerequisite(wrong)


if __name__ == "__main__":
    unittest.main()
