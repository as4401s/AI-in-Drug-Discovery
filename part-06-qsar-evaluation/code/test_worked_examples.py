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
        """The drawn loss bowl must evaluate the very objective used by the parameter walk."""
        payload = self.lab().build_payload()
        self.assertIn("bowl_grid", payload["parameter_learning"])
        self.assertEqual(payload["parameter_learning"]["bowl_grid"], [
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
        self.assertEqual([row["parameter"] for row in payload["parameter_learning"]["trace"]], [0, 0.6, 1.08, 1.464])
        self.assertEqual([row["loss"] for row in payload["parameter_learning"]["trace"]], [9, 5.76, 3.6864, 2.359296])
        self.assertAlmostEqual(payload["illustrative_regression"]["scores"]["mae"], 1 / 3)
        self.assertEqual(payload["illustrative_regression"]["scores"]["r2"], 0.75)
        self.assertAlmostEqual(payload["untied_ranking"]["rho"], 0.8)
        self.assertEqual(payload["measured_reference"]["activity_id"], 13852013)
        self.assertAlmostEqual(payload["measured_reference"]["pic50"], 8.585026652029182)
        self.assertIn("shifted_fold_ratio", payload["individual_log_error"])
        self.assertEqual(payload["individual_log_error"]["shifted_fold_ratio"], 100)

    def test_learning_rate_comparison_matches_the_video(self):
        """Rate 0.5 lands on three; rate 1.1 overshoots and the loss rises."""
        lab = self.lab()
        small = lab.descent_path(0, 0.1, 3)
        self.assertEqual([row["w"] for row in small], [0, 0.6, 1.08, 1.464])
        self.assertEqual(lab.descent_path(0, 0.5, 1)[-1], {"w": 3, "loss": 0})
        large = lab.descent_path(0, 1.1, 2)
        self.assertEqual([row["w"] for row in large], [0, 6.6, -1.32])
        self.assertEqual([row["loss"] for row in large], [9, 12.96, 18.6624])
        with self.assertRaises(ValueError):
            lab.descent_path(0, 0.1, 0)

    def test_epoch_counts_updates_per_batch(self):
        """One thousand examples in batches of one hundred give ten updates."""
        lab = self.lab()
        self.assertEqual(lab.updates_per_epoch(1000, 100), 10)
        self.assertEqual(lab.updates_per_epoch(1050, 100), 11)
        with self.assertRaises(ValueError):
            lab.updates_per_epoch(0, 100)

    def test_boosting_adds_half_of_the_remaining_difference(self):
        """Targets 4, 6, 8 start at 6, leave -2, 0, +2 and move to 5, 6, 7."""
        round_ = self.lab().boosting_round([4, 6, 8], 0.5)
        self.assertEqual(round_["first_prediction"], [6, 6, 6])
        self.assertEqual(round_["remaining"], [-2, 0, 2])
        self.assertEqual(round_["new_prediction"], [5, 6, 7])

    def test_centring_uses_the_training_mean_only(self):
        """A held-aside value of ten becomes four, not three, so it does not set its own scale."""
        result = self.lab().centre_with_training_mean([4, 6, 8], [10])
        self.assertEqual(result["training_mean"], 6)
        self.assertEqual(result["centred_training"], [-2, 0, 2])
        self.assertEqual(result["centred_held_aside"], [4])
        self.assertEqual(result["leaked_mean_for_comparison"], 7)

    def test_distance_groups_and_interval_coverage(self):
        """Error rises with distance in the schematic rows, and nine of ten references fall inside."""
        payload = self.lab().build_payload()
        maes = [group["mae"] for group in payload["neighbour_distance_groups"]["groups"]]
        self.assertEqual(maes, sorted(maes))
        for got, want in zip(maes, [0.3, 0.45, 0.75, 1.15]):
            self.assertAlmostEqual(got, want)
        coverage = payload["interval_coverage"]
        self.assertEqual((coverage["inside"], coverage["total"]), (9, 10))
        self.assertEqual(coverage["outside_rows"], [3])
        with self.assertRaises(ValueError):
            self.lab().interval_coverage([1, 2], [0], [3, 4])


if __name__ == "__main__":
    unittest.main()
