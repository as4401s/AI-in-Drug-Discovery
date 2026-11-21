"""Check the number table X, the label join and the nearest-neighbor similarity.

What it needs
    Python 3.10 or newer and NumPy.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""
import unittest

import numpy as np

from model_inputs import make_matrix, match_labels, nearest_support


class ModelInputsTest(unittest.TestCase):
    def setUp(self):
        """Two small molecules with made-up fingerprint positions and descriptors."""
        self.features = [
            {"standard_inchi_key": "A", "morgan_on_bits": [1, 3, 5], "maccs_on_bits": [2],
             "MolWt": 123.5, "MolLogP": 0.6, "TPSA": 18, "HBD": 1, "HBA": 1,
             "heavy_atoms": 7, "rotatable_bonds": 0},
            {"standard_inchi_key": "B", "morgan_on_bits": [1, 5, 7], "maccs_on_bits": [2, 3],
             "MolWt": 167.25, "MolLogP": 1.2, "TPSA": 23, "HBD": 0, "HBA": 2,
             "heavy_atoms": 11, "rotatable_bonds": 1},
        ]

    def test_matrix_preserves_the_documented_positions_and_feature_order(self):
        """Bits land in their columns, descriptors come last, and an out-of-range bit position raises an error."""
        matrix = make_matrix(self.features)
        self.assertEqual(matrix.shape, (2, 2222))
        self.assertEqual(np.flatnonzero(matrix[0, :2048]).tolist(), [1, 3, 5])
        self.assertEqual(np.flatnonzero(matrix[1, 2048:2215]).tolist(), [2, 3])
        np.testing.assert_allclose(matrix[0, 2215:], [123.5, 0.6, 18.0, 1, 1, 7, 0])
        self.features[0]["morgan_on_bits"] = [2048]
        with self.assertRaisesRegex(ValueError, "Morgan"):
            make_matrix(self.features)

    def test_labels_use_structural_identity_and_keep_feature_order(self):
        """Labels are matched by identity, not by position; missing or duplicate identities raise errors."""
        labels = [{"inchikey": "B", "pic50": 7.1}, {"inchikey": "A", "pic50": 6.2}]
        np.testing.assert_allclose(match_labels(self.features, labels), [6.2, 7.1])
        with self.assertRaisesRegex(ValueError, "same structural identities"):
            match_labels(self.features, labels[:1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            match_labels(self.features, labels + labels[-1:])

    def test_similarity_uses_the_best_training_neighbour(self):
        """Tanimoto {1,3,5} with {1,5,7} is 2/4 = 0.5; ties are broken by sorted identity."""
        result = nearest_support([1, 3, 5], {"B": [1, 5, 7], "C": [3]})
        self.assertEqual(result, ("B", 0.5))
        result = nearest_support([1, 3, 5], {"B": [1, 5, 7], "A": [1, 5, 7]})
        self.assertEqual(result, ("A", 0.5))


if __name__ == "__main__":
    unittest.main()
