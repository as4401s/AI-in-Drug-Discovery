"""Check that the activity-curation step keeps only comparable, exact measurements and merges duplicates by structure.

What it needs
    Python 3.10 or newer and RDKit.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""

import unittest

from curate_assays import curate


def activity(i, **updates):
    """Build a small mock row resembling the declared public ChEMBL response."""
    return dict({
        "activity_id": i, "assay_chembl_id": "ASSAY", "target_chembl_id": "CHEMBL203",
        "assay_variant_mutation": None, "data_validity_comment": None, "potential_duplicate": 0,
        "molecule_chembl_id": "MOL" + str(i), "parent_molecule_chembl_id": "MOL" + str(i),
        "canonical_smiles": "Cc1ccccc1", "standard_value": "100", "standard_units": "nM",
        "standard_relation": "=", "standard_type": "IC50",
    }, **updates)


class CurationTests(unittest.TestCase):
    def test_filtered_rows_and_duplicate_identity(self):
        """Rows 1 and 2 are the same structure written differently, so they merge; rows 3 to 8 each break one rule."""
        observations, rejected = curate([
            activity(1), activity(2, canonical_smiles="c1cc(C)ccc1", standard_value="10"),
            activity(3, standard_relation=">"), activity(4, standard_units="uM"),
            activity(5, assay_variant_mutation="L858R"), activity(6, canonical_smiles="C.O"),
            activity(7, standard_value="NaN"), activity(8, assay_chembl_id="OTHER"),
        ], "CHEMBL203", None, {"ASSAY"})
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["pic50"], 7.5)
        self.assertEqual(observations[0]["source_activity_ids"], [1, 2])
        self.assertEqual([x["activity_id"] for x in rejected], [3, 4, 5, 6, 7, 8])

    def test_kras_requires_the_exact_variant(self):
        """Only the G12D measurement is kept; the G12C row belongs to a different experiment."""
        observations, _ = curate([
            activity(1, target_chembl_id="CHEMBL2189121", assay_variant_mutation="G12D"),
            activity(2, target_chembl_id="CHEMBL2189121", assay_variant_mutation="G12C"),
        ], "CHEMBL2189121", "G12D", {"ASSAY"})
        self.assertEqual(observations[0]["source_activity_ids"], [1])
