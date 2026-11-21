"""Protect the holdout rules and the worked finite-sample interval calculation.

What it needs
    Python 3.10 or newer and NumPy.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""

import json
import math
import unittest

from evaluation import calibration_width, regression_metrics, split_membership


class EvaluationTests(unittest.TestCase):
    def test_deterministic_scaffold_isolation(self):
        """The same seed gives the same split, every row is used once and no scaffold is shared between sets."""
        keys = [f"M{i}" for i in range(27)]
        groups = [f"S{i // 3}" for i in range(27)]
        membership = split_membership(keys, groups, "scaffold", seed=31)
        self.assertEqual(membership, split_membership(keys, groups, "scaffold", seed=31))
        self.assertEqual(sorted(i for role in membership.values() for i in role), list(range(27)))
        group_sets = [{groups[i] for i in membership[name]} for name in ("development", "calibration", "test")]
        self.assertGreaterEqual(len(group_sets[1]), 4)
        self.assertTrue(group_sets[0].isdisjoint(group_sets[1] | group_sets[2]))
        self.assertTrue(group_sets[1].isdisjoint(group_sets[2]))
        json.dumps(membership)

    def test_random_split_holds_identity(self):
        """A random split uses every row once and refuses duplicate identities."""
        keys = [f"M{i}" for i in range(24)]
        membership = split_membership(keys, ["all"] * len(keys), "random", seed=31)
        self.assertEqual(sorted(sum(membership.values(), [])), list(range(24)))
        with self.assertRaises(ValueError):
            split_membership(["same"] * 24, ["all"] * 24, "random", seed=31)

    def test_calibration_uses_worst_error_per_group(self):
        """Group B has two errors; only the larger one (0.80) counts, and the rank-4 score is the half-width."""
        data = [0.25, 0.80, 0.15, 0.40, 0.54]
        result = calibration_width(data, ["A", "B", "C", "D", "B"], coverage=0.8)
        self.assertEqual(result["ordered_scores"], [0.15, 0.25, 0.40, 0.80])
        self.assertEqual(result["rank"], 4)
        self.assertEqual(result["half_width"], 0.80)
        with self.assertRaises(ValueError):
            calibration_width([0.2, 0.5], ["A", "B"], coverage=0.9)

    def test_regression_metrics_use_measured_values_and_signed_errors(self):
        """Predictions [6, 8, 7] for measurements [6, 7, 8]: MAE 2/3, RMSE sqrt(2/3), R squared 0, Spearman 0.5."""
        metrics = regression_metrics([6.0, 7.0, 8.0], [6.0, 8.0, 7.0])
        self.assertAlmostEqual(metrics["mae"], 2.0 / 3.0)
        self.assertAlmostEqual(metrics["rmse"], math.sqrt(2.0 / 3.0))
        self.assertEqual(metrics["r2"], 0.0)
        self.assertAlmostEqual(metrics["spearman"], 0.5)

    def test_rank_metrics_handle_ties_and_flat_folds(self):
        """Tied values share an average rank; a flat column gives no R squared or Spearman value (None)."""
        tied = regression_metrics([6.0, 6.0, 8.0, 9.0], [6.0, 7.0, 8.0, 9.0])
        self.assertAlmostEqual(tied["spearman"], 0.9486832980505138)
        self.assertIsNone(regression_metrics([7.0] * 3, [6.0, 7.0, 8.0])["r2"])
        self.assertIsNone(regression_metrics([6.0, 7.0, 8.0], [7.0] * 3)["spearman"])
