"""Cross-check the small lesson calculations independently of the assay data.

What it needs
    Python 3.10 or newer and NumPy.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""

import math
import unittest

from worked_examples import examples


class WorkedExamplesTests(unittest.TestCase):
    def test_tree_updates_and_calibration(self):
        """Tree leaf averages, forest average, boosting correction and the calibration interval match the video."""
        result = examples()
        self.assertEqual(result["potency"], [7, 8])
        self.assertEqual(result["tree"]["leaf_predictions"], [6.5, 8.5])
        self.assertEqual(result["forest"]["prediction"], 7)
        self.assertEqual(result["boosting"]["initial_residuals"], [-1, 1])
        self.assertEqual(result["boosting"]["predictions"], [6.5, 7.5])
        self.assertEqual(result["boosting"]["mse_before"], 1.0)
        self.assertEqual(result["boosting"]["mse_after"], 0.25)
        self.assertEqual(result["calibration"]["ordered_rank"], 4)
        self.assertEqual(result["calibration"]["interval"], [6.2, 7.8])

    def test_neural_and_graph_values(self):
        """The one-step neural network update and the C-C-O message-passing numbers match the video."""
        result = examples()
        self.assertEqual(result["mlp"]["prediction"], 1)
        self.assertEqual(result["mlp"]["gradient"], -2)
        self.assertAlmostEqual(result["mlp"]["next_loss"], 0.64)
        self.assertEqual(result["graph"]["neighbor_means"], [1, 1.5, 1])
        self.assertEqual(result["graph"]["hidden"], [1.5, 2, 2])
        self.assertTrue(math.isclose(result["graph"]["prediction"], 6.2))
