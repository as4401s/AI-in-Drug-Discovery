"""Check that the feature handoff matches the Part 5 molecular representation and refuses a wrong identity.

What it needs
    Python 3.10 or newer and RDKit.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK). The toy molecule is ethanol (SMILES CCO, formula C2H6O, molecular weight 46.069).
"""
import unittest

from feature_handoff import feature_rows


class FeatureHandoffTest(unittest.TestCase):
    def test_features_match_the_approved_molecular_representation(self):
        """Ethanol gets the expected formula, weight, donor count and fingerprint positions, and no measurement column."""
        rows = feature_rows([{
            "compound_id": "TOY-1",
            "smiles": "CCO",
            "inchikey": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
            "pic50": 8.123456,
        }])
        self.assertEqual(len(rows), 1)
        ethanol = rows[0]
        self.assertEqual(ethanol["formula"], "C2H6O")
        self.assertAlmostEqual(ethanol["MolWt"], 46.069, places=3)
        self.assertEqual(ethanol["HBD"], 1)
        self.assertEqual(ethanol["morgan_on_bits"], [80, 222, 294, 807, 1057, 1410])
        self.assertEqual(ethanol["maccs_on_bits"], [82, 109, 114, 139, 153, 155, 157, 160, 164])
        self.assertNotIn("pic50", ethanol)

    def test_checks_identity_before_passing_features_to_the_training_lesson(self):
        """A wrong InChIKey stops the export before any features are passed on."""
        row = {"compound_id": "TOY-1", "smiles": "CCO", "inchikey": "WRONG"}
        with self.assertRaisesRegex(ValueError, "TOY-1.*identity"):
            feature_rows([row])


if __name__ == "__main__":
    unittest.main()
