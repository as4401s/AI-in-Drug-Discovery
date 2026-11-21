"""Check the fingerprint distance, the Butina clusters and the MaxMin choices on tiny inputs that can be verified by hand.

What it needs
    Python 3.10 or newer, NumPy and RDKit.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""
import unittest

from selection import butina_clusters, distance_matrix, maxmin, selection_summary


class TestScreening(unittest.TestCase):
    def test_rdkit_uses_tanimoto_distance_of_binary_bits(self):
        """Bit sets {1,3,5} and {1,5,7} share 2 of 4 bits, so the distance is 0.5; a set with no shared bit has distance 1."""
        distances = distance_matrix([[1, 3, 5], [1, 5, 7], [8]])
        self.assertEqual(distances.tolist(), [[0.0, 0.5, 1.0], [0.5, 0.0, 1.0], [1.0, 1.0, 0.0]])

    def test_butina_centroid_is_an_actual_member(self):
        """The first number of each cluster is a real molecule, and two molecules farther than 0.34 apart are not neighbors."""
        matrix = distance_matrix([[1, 2], [1, 2, 3], [1, 3], [8, 9], [8, 9, 10]])
        clusters = butina_clusters(matrix, 0.34)
        self.assertEqual(clusters[0][0], 1)
        self.assertEqual(set(clusters[0]), {0, 1, 2})
        self.assertEqual(clusters[1][0], 4)
        self.assertEqual(set(clusters[1]), {3, 4})
        self.assertGreater(matrix[0, 2], 0.34)

    def test_maxmin_updates_the_nearest_distance_after_each_pick(self):
        """After A and C are chosen, the third slot compares B, D and E by their distance to the nearest chosen molecule."""
        rows = [{"compound_id": name, "predicted_pic50": prediction}
                for name, prediction in zip("ABCDE", [8, 7.9, 7.7, 7.6, 7.4])]
        distances = distance_matrix([[1, 2], [1, 2, 3], [7, 8], [1, 7], [3, 4]])
        chosen, trace = maxmin(rows, distances, [0, 1, 2, 3, 4], 3)
        self.assertEqual(chosen, [0, 2, 4])
        third_distances = {row["id"]: row["min_distance_to_selected"] for row in trace[2]["options"]}
        self.assertAlmostEqual(third_distances["B"], 1 / 3)
        self.assertAlmostEqual(third_distances["D"], 2 / 3)
        self.assertEqual(third_distances["E"], 1.0)
        self.assertEqual(selection_summary(rows, distances, chosen)["mean_pairwise_distance"], 1.0)

    def test_budget_never_pads_an_insufficient_rep_set(self):
        """Asking for 20 picks from one candidate returns that one candidate and does not invent others."""
        rows = [{"compound_id": "A", "predicted_pic50": 8.0}]
        chosen, trace = maxmin(rows, distance_matrix([[1]]), [0], 20)
        self.assertEqual(chosen, [0])
        self.assertEqual(len(trace), 1)
