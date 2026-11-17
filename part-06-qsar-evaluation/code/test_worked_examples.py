"""Check meaningful scientific boundaries in the real, offline lesson arithmetic."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

import numpy as np


class WorkedExamplesTests(unittest.TestCase):
    """Catch invalid measurements, misleading metrics and identity leakage."""

    def lab(self):
        """Load the adjacent implementation after an explicit missing-file assertion."""
        path = Path(__file__).with_name("worked_examples.py")
        self.assertTrue(path.is_file(), "The runnable arithmetic companion is missing")
        spec = importlib.util.spec_from_file_location("worked_examples", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_nonpositive_or_nonfinite_concentration_has_no_exact_pic50(self):
        """A zero, negative or missing-scale measurement must not become a label."""
        lab = self.lab()
        for value in [0, -1, float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                lab.pic50_from_nm(value)
        self.assertEqual(lab.pic50_from_nm(100), 7.0)

    def test_constant_reference_r2_is_reported_as_undefined(self):
        """A degenerate test set must not produce a reassuring finite R squared."""
        lab = self.lab()
        for predictions in [[7, 7], [6, 8]]:
            scores = lab.regression_scores([7, 7], predictions)
            self.assertIsNone(scores["r2"])
            self.assertEqual(scores["r2_status"], "undefined_constant_reference")

    def test_pic50_inverse_roundtrips_the_concentration_units(self):
        """The inverse logarithm must restore nM rather than molar concentrations."""
        lab = self.lab()
        self.assertTrue(hasattr(lab, "nm_from_pic50"), "The inverse conversion is missing")
        for pic50, expected_nm in [(8, 10), (7, 100), (6, 1000)]:
            self.assertEqual(lab.nm_from_pic50(pic50), expected_nm)
        self.assertAlmostEqual(lab.nm_from_pic50(lab.pic50_from_nm(2.6)), 2.6)
        with self.assertRaises(ValueError):
            lab.nm_from_pic50(float("nan"))

    def test_loss_bowl_and_update_trace_use_the_same_objective(self):
        """The drawn loss bowl must evaluate the very objective used by the knob walk."""
        payload = self.lab().build_payload()
        self.assertIn("bowl_grid", payload["knob_learning"])
        self.assertEqual(payload["knob_learning"]["bowl_grid"], [
            {"parameter": 0, "loss": 9}, {"parameter": 1, "loss": 4},
            {"parameter": 2, "loss": 1}, {"parameter": 3, "loss": 0}])

    def test_constant_prediction_has_undefined_spearman(self):
        """A mean baseline supplies no ranking, even when its value is useful."""
        lab = self.lab()
        self.assertIsNone(lab.spearman_scores([6, 7, 8], [6, 6, 6])["rho"])
        self.assertIsNone(lab.spearman_scores([7, 7, 7], [6, 7, 8])["rho"])

    def test_tied_values_receive_average_rank(self):
        """A sort order must not invent an ordering between equally valued examples."""
        lab = self.lab()
        np.testing.assert_array_equal(lab.average_ranks([4, 2, 2, 9]), [3, 1.5, 1.5, 4])
        self.assertAlmostEqual(lab.spearman_scores([1, 2, 2, 4], [4, 2, 2, 1])["rho"], -1)

    def test_baseline_uses_training_labels_while_r2_uses_reference_mean(self):
        """Using held-out targets to fit the baseline would change six into seven."""
        lab = self.lab()
        predictions = lab.training_mean_predictions([5, 6, 7], 3)
        np.testing.assert_array_equal(predictions, [6, 6, 6])
        scores = lab.regression_scores([6, 7, 8], predictions)
        self.assertEqual(scores["reference_mean"], 7)
        self.assertEqual(scores["mae"], 1)
        self.assertEqual(scores["r2"], -1.5)
        self.assertAlmostEqual(scores["rmse"], 1.2909944487358056)

    def test_metric_results_preserve_large_value_error_despite_perfect_order(self):
        """A rank score alone must not conceal a two-unit numerical offset."""
        lab = self.lab()
        scores = lab.regression_scores([6, 7, 8, 9], [8, 9, 10, 11])
        self.assertEqual(scores["mae"], 2)
        self.assertEqual(scores["rmse"], 2)
        self.assertAlmostEqual(scores["r2"], -2.2)
        self.assertAlmostEqual(lab.spearman_scores([6, 7, 8, 9], [8, 9, 10, 11])["rho"], 1)

    def test_metrics_reject_unmatched_or_missing_reference_rows(self):
        """An omitted prediction or NaN must not silently change the evaluated panel."""
        lab = self.lab()
        for reference, predicted in [([6, 7], [6]), ([], []), ([6, float("nan")], [6, 7])]:
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                lab.regression_scores(reference, predicted)

    def test_duplicate_identity_is_kept_in_one_partition(self):
        """Two strings naming the same canonical identity must not cross partitions."""
        lab = self.lab()
        counts = lab.check_identity_partitions({"train": ["identity-A", "identity-A"], "test": ["identity-B"]})
        self.assertEqual(counts["train"]["unique_identities"], 1)
        with self.assertRaises(ValueError):
            lab.check_identity_partitions({"train": ["identity-A"], "test": ["identity-A"]})
        with self.assertRaises(ValueError):
            lab.check_identity_partitions({"train": [""]})

    def test_frozen_payload_matches_the_hand_examples(self):
        """Changed optimization or residual definitions must change a checked result."""
        lab = self.lab()
        payload = lab.build_payload()
        self.assertEqual([row["parameter"] for row in payload["knob_learning"]["trace"]], [0, 0.6, 1.08, 1.464])
        self.assertEqual([row["loss"] for row in payload["knob_learning"]["trace"]], [9, 5.76, 3.6864, 2.359296])
        self.assertAlmostEqual(payload["illustrative_regression"]["scores"]["mae"], 1 / 3)
        self.assertEqual(payload["illustrative_regression"]["scores"]["r2"], 0.75)
        self.assertAlmostEqual(payload["untied_ranking"]["rho"], 0.8)
        self.assertEqual(payload["measured_reference"]["activity_id"], 13852013)
        self.assertAlmostEqual(payload["measured_reference"]["pic50"], 8.585026652029182)
        self.assertIn("shifted_fold_ratio", payload["individual_log_error"])
        self.assertEqual(payload["individual_log_error"]["shifted_fold_ratio"], 100)


if __name__ == "__main__":
    unittest.main()
