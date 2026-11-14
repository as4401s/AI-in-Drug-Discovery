"""Offline checks of the real-record curation (Part 4)

These tests use the saved ChEMBL files, so they need no internet and no model provider. They prove that
each rule of curate_activities.py does what the lesson says on real records.

BEFORE YOU RUN THEM
  curate_activities.py also hash-checks six background documents that are not stored in this repository.
  Run  python code/fetch_sources.py  once (internet needed) to download them.

HOW TO RUN IT
  python -m unittest discover -s code -p "test_curate_activities.py" -v
"""

# unittest runs the checks; copy makes an edited copy of a record for the failure test.
import copy
import unittest

# build_table() makes the full table; classify() applies the rules to one record.
from curate_activities import build_table, classify


class CurationTests(unittest.TestCase):
    """Checks of the curation rules on the 12 selected real records."""
    @classmethod
    def setUpClass(cls):
        """Build the curation table once and index its rows by activity ID."""
        cls.result = build_table()
        cls.rows = {r["activity_id"]: r for r in cls.result["rows"]}

    def test_real_records_remain_in_separate_assays(self):
        """209 rows were acquired, 12 selected, exactly one retained (activity 13852013, 2.6 nM, confidence 9)."""
        self.assertEqual(self.result["acquired_source_row_count"], 209)
        self.assertEqual(len(self.rows), 12)
        retained = [r for r in self.rows.values() if r["curation_status"].startswith("retained")]
        self.assertEqual([r["activity_id"] for r in retained], [13852013])
        self.assertEqual(retained[0]["standard_value"], 2.6)
        self.assertEqual(retained[0]["confidence_score"], 9)
        self.assertIsNone(retained[0]["construct_sequence"])

    def test_censored_is_not_an_exact_training_label(self):
        """A '> 1000' record keeps its relation and gets no point pIC50 and no pooling group."""
        row = self.rows[2943660]
        self.assertEqual(row["standard_relation"], ">")
        self.assertEqual(row["standard_value"], 1000)
        self.assertIsNone(row["pIC50_exact_point"])
        self.assertEqual(row["variant"], "T790M")
        self.assertIsNone(row["pooling_group"])

    def test_missing_is_not_imputed_zero(self):
        """A record with no value keeps None; it is never turned into zero."""
        row = self.rows[14974603]
        self.assertIsNone(row["standard_value"])
        self.assertIsNone(row["pIC50_exact_point"])
        self.assertEqual(row["activity_comment"], "Not Determined")

    def test_assay_letter_does_not_override_cell_context(self):
        """An assay typed 'B' (binding) can still be a cell-based result; the cell line and exposure time decide."""
        row = self.rows[13446008]
        self.assertEqual(row["assay_type"], "B")
        self.assertEqual(row["cell_line"], "LoVo")
        self.assertEqual(row["exposure_minutes"], 120)
        self.assertEqual(row["curation_status"], "excluded_context")

    def test_confidence_and_unknown_variant_are_explicit(self):
        """A confidence score below 9 and an unknown EGFR variant each have their own exclusion status."""
        self.assertEqual(self.rows[3261330]["curation_status"], "excluded_target_confidence")
        self.assertEqual(self.rows[3261330]["confidence_score"], 8)
        self.assertEqual(self.rows[1682080]["variant"], "unknown")
        self.assertEqual(self.rows[1682080]["curation_status"], "excluded_unknown_variant")

    def test_wrong_chemical_identity_cannot_be_retained(self):
        """A record for a different compound ID is excluded for identity, whatever else is true."""
        # A minimal valid erlotinib/EGFR record, used to build a bad variant of it below.
        row = {"molecule_chembl_id": "CHEMBL553", "target_chembl_id": "CHEMBL203", "standard_type": "IC50",
               "standard_units": "nM", "standard_value": "2.6", "standard_relation": "=", "potential_duplicate": 0}
        # Copy the record and swap in a different compound ID.
        wrong = copy.deepcopy(row)
        wrong["molecule_chembl_id"] = "CHEMBL4858364"
        status, _ = classify(wrong, {"confidence_score": 9}, "reference_explicit_wild_type", "biochemical")
        self.assertEqual(status, "excluded_identity_or_endpoint")

    def test_nonpositive_or_nonfinite_concentration_is_refused(self):
        """Zero, negative, NaN and infinite concentrations are invalid potency labels."""
        # The same minimal record without a concentration; each invalid value is tried in turn.
        row = {"molecule_chembl_id": "CHEMBL553", "target_chembl_id": "CHEMBL203", "standard_type": "IC50",
               "standard_units": "nM", "standard_relation": "=", "potential_duplicate": 0}
        for invalid in ["0", "-1", "nan", "inf"]:
            status, _ = classify({**row, "standard_value": invalid}, {"confidence_score": 9}, "reference_explicit_wild_type", "biochemical")
            self.assertEqual(status, "excluded_invalid_value")


if __name__ == "__main__":
    unittest.main()
