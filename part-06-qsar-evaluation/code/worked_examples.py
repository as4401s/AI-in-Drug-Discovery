"""Reproduce the small numerical examples in AI in Drug Discovery, Part 6.

Needs Python and NumPy only. Run ``python code/worked_examples.py`` from the
part folder; the script prints the real results and saves deterministic JSON
under data/outputs/. All model, ranking and neighbour examples are numerical
teaching examples, with no invented measured labels attached to molecules.
The separate 2.6 nM erlotinib record keeps its original assay provenance.
This concepts companion fits a training-mean baseline; the displayed line,
tree leaves and forest values are specified arithmetic, not trained QSARs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def numeric_vector(values: Sequence[float], name: str) -> np.ndarray:
    """Require a nonempty finite vector so missing rows stay explicit failures."""
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0 or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a nonempty one-dimensional finite vector")
    return array


def pic50_from_nm(ic50_nm: float) -> float:
    """Convert one positive, exact IC50 in nM to its negative molar logarithm."""
    concentration = float(ic50_nm)
    if not np.isfinite(concentration) or concentration <= 0:
        raise ValueError("An exact IC50 must be finite and positive before taking a logarithm")
    # One nanomolar is 10^-9 molar, which supplies the nine in this formula.
    return float(9 - np.log10(concentration))


def nm_from_pic50(pic50: float) -> float:
    """Undo the logarithm and return an exact positive concentration in nM."""
    value = float(pic50)
    if not np.isfinite(value):
        raise ValueError("pIC50 must be finite before inverse conversion")
    with np.errstate(over="ignore", under="ignore"):
        concentration = float(np.power(10.0, 9 - value))
    if not np.isfinite(concentration) or concentration <= 0:
        raise ValueError("The converted concentration is outside finite positive numeric range")
    return concentration


def squared_knob_loss(parameter: float) -> float:
    """Evaluate the same generic squared objective for the bowl and learning walk."""
    return float((parameter - 3)**2)


def regression_scores(reference: Sequence[float], predicted: Sequence[float]) -> dict[str, Any]:
    """Measure errors on matched references; preserve undefined R squared as null."""
    truth = numeric_vector(reference, "reference")
    estimate = numeric_vector(predicted, "predicted")
    if truth.shape != estimate.shape:
        raise ValueError("Each reference row needs exactly one corresponding prediction")
    # Fix one sign convention: residual equals prediction minus reference.
    residual = estimate - truth
    squared_error = float(np.sum(residual**2))
    reference_mean = float(np.mean(truth))
    total_variation = float(np.sum((truth - reference_mean)**2))
    if truth.size < 2:
        r2, status = None, "undefined_fewer_than_two_references"
    elif total_variation == 0:
        r2, status = None, "undefined_constant_reference"
    else:
        r2, status = float(1 - squared_error / total_variation), "defined"
    return {
        "residual_convention": "prediction minus reference",
        "residuals": residual.tolist(),
        "absolute_errors": np.abs(residual).tolist(),
        "squared_errors": (residual**2).tolist(),
        "reference_mean": reference_mean,
        "sse": squared_error,
        "tss": total_variation,
        "mae": float(np.mean(np.abs(residual))),
        "mse": float(np.mean(residual**2)),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "r2": r2,
        "r2_status": status,
    }


def training_mean_predictions(training_labels: Sequence[float], prediction_count: int) -> list[float]:
    """Fit the mean using training labels, then repeat it for new feature rows."""
    training = numeric_vector(training_labels, "training labels")
    if isinstance(prediction_count, bool) or not isinstance(prediction_count, int) or prediction_count < 1:
        raise ValueError("prediction_count must be a positive integer")
    # The function receives a count of new rows, not their held-out labels.
    return [float(np.mean(training))] * prediction_count


def average_ranks(values: Sequence[float]) -> np.ndarray:
    """Rank low to high, giving tied values the mean of their occupied positions."""
    data = numeric_vector(values, "rank values")
    order = np.argsort(data, kind="stable")
    ranks = np.empty(data.size, dtype=float)
    start = 0
    while start < data.size:
        end = start + 1
        while end < data.size and data[order[end]] == data[order[start]]:
            end += 1
        # Positions are one-based: indices start..end-1 occupy start+1..end.
        ranks[order[start:end]] = ((start + 1) + end) / 2
        start = end
    return ranks


def spearman_scores(reference: Sequence[float], predicted: Sequence[float]) -> dict[str, Any]:
    """Correlate average ranks; a constant vector supplies no defined ordering."""
    truth_ranks = average_ranks(reference)
    predicted_ranks = average_ranks(predicted)
    if truth_ranks.shape != predicted_ranks.shape:
        raise ValueError("Ranking needs equal numbers of references and predictions")
    centered_truth = truth_ranks - truth_ranks.mean()
    centered_prediction = predicted_ranks - predicted_ranks.mean()
    denominator = float(np.sqrt(np.sum(centered_truth**2) * np.sum(centered_prediction**2)))
    if denominator == 0:
        rho, status = None, "undefined_constant_rank_vector"
    else:
        rho = float(np.sum(centered_truth * centered_prediction) / denominator)
        status = "defined"
    return {"reference_ranks": truth_ranks.tolist(), "predicted_ranks": predicted_ranks.tolist(),
            "rho": rho, "status": status}


def check_identity_partitions(partitions: Mapping[str, Sequence[str]]) -> dict[str, dict[str, int]]:
    """Refuse an exact supplied identity appearing in more than one partition.

    Identity keys must already come from the chosen chemistry identity policy.
    This string guard groups aliases/replicates; it does not infer a molecular
    identity from names or establish chemical dissimilarity across partitions.
    """
    owners: dict[str, str] = {}
    summary = {}
    for partition, identities in partitions.items():
        unique = set()
        for identity in identities:
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError("Every row needs a nonempty verified identity key")
            if identity in owners and owners[identity] != partition:
                raise ValueError(f"Identity {identity!r} crosses {owners[identity]!r} and {partition!r}")
            owners[identity] = partition
            unique.add(identity)
        summary[partition] = {"rows": len(identities), "unique_identities": len(unique)}
    return summary


def build_payload() -> dict[str, Any]:
    """Calculate each frozen lesson example and keep its scientific scope beside it."""
    arithmetic_scope = "Illustrative numerical teaching example; no experimentally measured molecule labels"
    training_labels = [5, 6, 7]
    references = [6, 7, 8]
    line_inputs = np.array([-1, 0, 1], dtype=float)
    predictions = (7 + 0.5 * line_inputs).tolist()
    baseline = training_mean_predictions(training_labels, len(references))

    # Reuse the earlier course's generic knob, independently of molecular data.
    parameter, trace = 0.0, []
    for step in range(4):
        trace.append({"step": step, "parameter": round(parameter, 12),
                      "loss": round(squared_knob_loss(parameter), 12),
                      "gradient": round(2 * (parameter - 3), 12)})
        parameter -= 0.1 * 2 * (parameter - 3)

    # These two rows were deliberately defined as arithmetic sets in Part 5.
    first_bits, second_bits = {1, 3, 5}, {1, 5, 7}
    common, union = first_bits & second_bits, first_bits | second_bits
    similarity = len(common) / len(union)
    neighbours = [0.8, 0.5, 0.2]
    shifted_reference = [6, 7, 8, 9]
    shifted_prediction = [8, 9, 10, 11]
    untied_ranking = spearman_scores([1, 2, 3, 4], [1, 3, 2, 4])
    rank_differences = np.array(untied_ranking["reference_ranks"]) - np.array(untied_ranking["predicted_ranks"])

    # This real record is retained separately from all illustrative labels.
    measured = json.loads((ROOT / "data/raw/retained_erlotinib_reference.json").read_text())
    measured["pic50"] = pic50_from_nm(measured["ic50_nm"])
    return {
        "schema_version": "1.0.0", "episode": 6,
        "scope": "QSAR concepts and checked arithmetic; no empirical potency model training or benchmark",
        "concentration_conversion": {"scope": "Unit-conversion inputs, not new assay measurements",
            "formula": "pIC50 = 9 - log10(IC50 in nM)", "nm": [10, 100, 1000],
            "pic50": [pic50_from_nm(value) for value in [10, 100, 1000]],
            "inverse_formula": "IC50 in nM = 10^(9 - pIC50)",
            "inverse_pic50": [8, 7, 6], "roundtrip_nm": [nm_from_pic50(value) for value in [8, 7, 6]]},
        "measured_reference": measured,
        "knob_learning": {"scope": "Generic optimization arithmetic, separate from molecular prediction",
            "loss": "(w - 3)^2", "gradient": "2 * (w - 3)", "learning_rate": 0.1,
            "trace": trace, "display_rounding_decimal_places": 12,
            "bowl_grid": [{"parameter": value, "loss": squared_knob_loss(value)} for value in [0, 1, 2, 3]]},
        "training_mean_baseline": {"scope": arithmetic_scope,
            "training_labels": training_labels, "fitted_mean": float(np.mean(training_labels)),
            "evaluation_references": references, "predictions": baseline,
            "scores": regression_scores(references, baseline),
            "ranking": spearman_scores(references, baseline)},
        "illustrative_regression": {"scope": arithmetic_scope,
            "rule": "Specified line y_hat = 7 + 0.5*x; not fitted to assay data",
            "intercept": 7, "slope": 0.5, "x": line_inputs.tolist(),
            "evaluation_references": references, "predictions": predictions,
            "scores": regression_scores(references, predictions)},
        "untied_ranking": {"scope": arithmetic_scope,
            **untied_ranking,
            "rank_differences": rank_differences.tolist(),
            "rank_difference_squared_sum": float(np.sum(rank_differences**2)), "n": 4},
        "shifted_ranking": {"scope": arithmetic_scope, "references": shifted_reference,
            "predictions": shifted_prediction, "scores": regression_scores(shifted_reference, shifted_prediction),
            "ranking": spearman_scores(shifted_reference, shifted_prediction)},
        "individual_log_error": {"scope": "Concentration ratio for one absolute pIC50 error",
            "absolute_pic50_error": 0.5, "fold_ratio": float(10**0.5),
            "shifted_absolute_pic50_error": 2, "shifted_fold_ratio": float(10**2)},
        "fingerprint_overlap": {"scope": "Arithmetic bit sets from Part 5, not molecule potency",
            "first": sorted(first_bits), "second": sorted(second_bits), "intersection": sorted(common),
            "union": sorted(union), "tanimoto": similarity},
        "neighbour_diagnostic": {"scope": "Schematic similarities; no calibrated acceptance threshold",
            "similarities_to_training": neighbours, "nearest_similarity": max(neighbours),
            "nearest_distance": round(1 - max(neighbours), 12)},
        "tree_and_forest_overview": {"scope": "Specified numerical leaf/ensemble arithmetic; models not fitted",
            "leaf_training_values": [6, 8], "leaf_mean": float(np.mean([6, 8])),
            "specified_tree_predictions": [6, 7, 8], "forest_mean": float(np.mean([6, 7, 8]))},
        "identity_partition_example": {"scope": "Schematic preverified identities, not compound names",
            "summary": check_identity_partitions({"training": ["identity-A", "identity-A"],
                                                   "validation": ["identity-B"], "test": ["identity-C"]})},
    }


def build_evaluation_plan() -> dict[str, Any]:
    """Describe the planned Part 7 experiment before acquiring data or measuring results."""
    return {
        "schema_version": "1.0.0", "producer_episode": 6, "consumer_episode": 7,
        "status": "PLANNED; dataset acquisition, model training and empirical evaluation remain future work",
        "question": "Estimate a defined potency endpoint for new compounds within an explicit experimental and chemical scope",
        "current_evidence": {
            "part5": "Eight unique structural teaching identities; feature matrix has no activity labels and is not training-ready",
            "part4": "One separate retained erlotinib assay record; the 209-row raw collection contains only erlotinib across 209 assays",
            "counts_or_model_scores_for_future_dataset": None,
        },
        "acquisition": {
            "policy": "First investigate a bounded multi-compound collection from one compatible human wild-type EGFR biochemical assay",
            "continuity_candidate_only": "CHEMBL3095060; compatibility, compound count and scaffold diversity require actual verification",
            "endpoint": "Exact IC50 in nM, transformed to pIC50 only after unit, relation and positivity checks",
            "retain": ["database release and service version", "raw response bytes and SHA256", "retrieval UTC and public source URL",
                       "activity ID", "compound ID", "raw and isomeric structural strings", "complete identity key",
                       "assay ID", "document ID and original DOI", "target accession and variant", "organism",
                       "construct", "ATP/substrate conditions", "exposure/incubation time", "assay format",
                       "raw and standardized endpoint, value, units and relation", "data validity flags", "potential duplicate flag"],
            "missingness": "Keep missing context explicit. Retain every exclusion and its reason. A missing value is not zero.",
            "censored_measurements": "Keep inequality relations as bounds; exact-point regression labels require the declared exact-value policy.",
            "compatibility": "Define the experimental question first. Preserve mutants, cellular outcomes and different assay protocols separately.",
            "replicates": "Preserve original records and group their chemical identity; any within-condition aggregation needs a predeclared justified policy.",
            "rights": "Preserve ChEMBL/EMBL-EBI attribution and CC BY-SA 3.0 terms for redistributed or adapted data; paper rights remain separate.",
        },
        "features_and_identity": {
            "recipe": "Start from the recorded Part 5 identity and representation settings and reassess them against the acquired task",
            "exact_identity_groups": "Keep aliases, replicate records and the same declared chemical identity within one partition",
            "chemistry_policy": "Declare salts/components, stereochemistry, protonation and tautomer handling; preserve raw inputs and transformations",
            "feature_order": "Save feature names, units, toolkit/version and fingerprint family, radius, length, chirality and other settings",
        },
        "partition_design": {
            "freeze_before_fitting": "Retain immutable row/identity assignments, seed, grouping algorithm and dataset hashes",
            "training": "Fit model parameters and the mean baseline using training labels",
            "validation": "Choose model settings and learned preprocessing using training/validation folds; refit transforms inside each training fold",
            "test": "Use held-out references for the final stated comparison after model choices are frozen",
            "random": "A within-collection interpolation question; report train/test identity and nearest-neighbour overlap",
            "scaffold": "A declared structural-framework stress test, conditional on enough useful groups; different cores may still be similar",
            "time": "Use trustworthy experimental/availability timestamps when present; label publication-year splits as a proxy",
            "study": "A study or assay-group transfer question only if that endpoint combination is scientifically justified",
            "unavailable_design": "Record why a proposed split is unsupported; do not invent timestamps, scaffolds, extra datasets or a performance gap",
        },
        "comparison": {
            "baseline": "Training-mean predictor on the exact same held-out rows as each candidate model",
            "learned_preprocessing": "Fit imputation, scaling, selection or target transforms within training folds; apply those learned transforms to held-out inputs",
            "candidate_models": "Choose transparent, task-appropriate models in Part 7; any additional package requires approval",
            "metrics": ["MAE", "RMSE", "R squared with held-out-reference mean denominator", "Spearman with average ranks for ties"],
            "undefined_cases": "Preserve constant-reference R squared or constant-vector Spearman as undefined with a reason",
            "retain": ["per-row reference and prediction", "residual sign convention", "error examples", "split sizes and label distribution",
                       "exact command, runtime/package versions and settings", "actual outputs and hashes", "variation across justified repeats when feasible"],
        },
        "coverage_and_limits": {
            "diagnostics": ["nearest training-neighbour similarity using fixed representation settings", "descriptor range and missingness",
                            "errors across justified chemistry/assay subgroups", "activity-cliff examples if compatible measured evidence supports them"],
            "domain_rule": "Calibrate any coverage/uncertainty rule with appropriate held-out or out-of-fold evidence; a universal similarity cutoff is not assumed",
            "interpretation": "The result estimates the specified assay endpoint within the evaluated scope. Experimental confirmation and other development endpoints are separate evidence.",
            "future_screening_handoff": "Pass model/split/metric definitions and applicability limits to Part 8 only after the actual Part 7 run",
        },
    }


def main() -> None:
    """Save the deterministic lesson output and print the same genuine JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/outputs/worked_examples.json")
    arguments = parser.parse_args()
    payload = build_payload()
    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(text)
    plan = json.dumps(build_evaluation_plan(), indent=2, sort_keys=True, allow_nan=False) + "\n"
    arguments.output.with_name("evaluation_plan.json").write_text(plan)
    print(text, end="")


if __name__ == "__main__":
    main()
