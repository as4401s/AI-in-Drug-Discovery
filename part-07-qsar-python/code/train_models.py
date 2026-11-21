"""Tune, compare, calibrate and save the Part 7 potency models for EGFR and KRAS G12D.

What this file does
    1. Loads the Part 5 feature table and the measured pIC50 values (assay_tables.load_tables).
    2. Splits the molecules twice: by random identity and by held-out scaffold (evaluation.split_membership).
    3. Tunes Random Forest, XGBoost, a multilayer perceptron and a molecular graph model, using cross-validation on development data only.
    4. Scores every model on the test set against a median baseline, averages the three tabular models into an ensemble,
       and calibrates an interval half-width on separate calibration groups.
    5. Saves the scaffold-split EGFR ensemble, with a manifest, so Part 8 can reload exactly this model.

What it needs
    Python 3.10 or newer, NumPy, SciPy, scikit-learn, XGBoost, joblib, PyArrow and RDKit, plus the Part 5 Parquet handoff folder.

What to expect
    One progress line per split and one JSON evaluation file per target in data/trained/. Training takes a few minutes on a laptop.

Run
    python code/train_models.py            (writes into data/trained/)
"""

import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path

import joblib
import numpy as np
from rdkit import Chem, rdBase
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, KFold, ParameterGrid
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from assay_tables import AssayTables, digest, load_tables
from evaluation import calibration_width, regression_metrics, split_membership
from graph_model import GraphBatch, fit_graph, graph_arrays, predict as predict_graph
from model_inputs import DESCRIPTORS, MACCS_BITS, MORGAN_BITS, nearest_support

# One fixed seed makes every split, model fit and shuffle repeatable.
SEED = 31
# The interval is calibrated so that about 80% of new scaffold groups fall inside it.
NOMINAL_COVERAGE = 0.8
# The fingerprint bits come first in each row; the descriptors start at this column.
BIT_COUNT = MORGAN_BITS + MACCS_BITS
MODEL_NAMES = ("random_forest", "xgboost", "mlp")
# The small grids of settings that cross-validation compares for each model.
SETTINGS = {
    "random_forest": {"max_depth": [5, None], "min_samples_leaf": [1, 3]},
    "xgboost": {"max_depth": [2, 4], "learning_rate": [0.05, 0.12]},
    "mlp": {"hidden_layer_sizes": [(16,), (24, 8)], "alpha": [0.01, 0.15]},
    "gnn": {"width": [12, 24], "steps": [180, 360]},
}
ROOT = Path(__file__).resolve().parent.parent
# The Part 5 handoff folder: the Parquet feature tables, built in Part 5 and read here.
DEFAULT_FEATURES = ROOT.parent / "part-05-molecules-as-data-smiles-fingerprints-and-graphs/data/handoff/parquet"


def write_json(path: Path, data: dict) -> None:
    """Write JSON to a temporary file first, then rename it, so a stopped run never leaves a half-written file."""
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    pending.replace(path)


def make_model(name: str, options: dict):
    """Create a fresh estimator so no fitted state crosses validation folds.

    name: 'random_forest', 'xgboost' or 'mlp'. options: the settings chosen from SETTINGS.
    """
    if name == "random_forest":
        # 120 decision trees whose predictions are averaged; each split looks at a random quarter of the columns.
        return RandomForestRegressor(n_estimators=120, max_features=0.25, random_state=SEED,
                                     n_jobs=1, **options)
    if name == "xgboost":
        # 100 small trees added one after another, each fitted to the correction the earlier trees still need.
        return XGBRegressor(objective="reg:squarederror", tree_method="hist", n_estimators=100,
                            subsample=0.85, colsample_bytree=0.65, reg_lambda=1.0,
                            random_state=SEED, n_jobs=1, **options)
    if name == "mlp":
        # Standardize only the descriptor columns (they have very different scales); the 0/1 bits pass through.
        numeric_scaler = ColumnTransformer([("descriptors", StandardScaler(), slice(BIT_COUNT, None))],
                                           remainder="passthrough")
        mlp = MLPRegressor(solver="lbfgs", random_state=SEED, max_iter=500, **options)
        # The target pIC50 is standardized too, and the prediction is converted back afterwards.
        return TransformedTargetRegressor(regressor=make_pipeline(numeric_scaler, mlp),
                                          transformer=StandardScaler())
    raise ValueError(f"Unknown tabular model {name}")


def graph_batch(graphs: list, indices: list[int]) -> GraphBatch:
    """Stack the graph arrays of the chosen molecules into one batch."""
    return GraphBatch.from_graphs([graphs[i] for i in indices])


def fit_predict(name: str, settings: dict, data: AssayTables, graphs: list, train: list[int], predict: list[int]):
    """Fit with the requested training rows and evaluate only the specified rows.

    train and predict are lists of row numbers, so the same function serves cross-validation and the final fit.
    """
    if name == "gnn":
        model, _ = fit_graph(graph_batch(graphs, train), data.labels[train], seed=SEED, **settings)
        return model, predict_graph(graph_batch(graphs, predict), model)
    model = make_model(name, settings).fit(data.matrix[train], data.labels[train])
    return model, model.predict(data.matrix[predict])


def cross_validate(name: str, data: AssayTables, graphs: list, folds: list[tuple]) -> tuple[dict, list]:
    """Return all candidate fold scores and the parameters with the lowest mean MAE."""
    candidates = []
    # Try every combination of settings in the grid.
    for options in ParameterGrid(SETTINGS[name]):
        errors = []
        # Each fold fits on some development rows and scores on the development rows held out of that fit.
        for train, validation in folds:
            _, predicted = fit_predict(name, options, data, graphs, train, validation)
            errors.append(regression_metrics(data.labels[validation], predicted)["mae"])
        candidates.append({"settings": options, "fold_mae": errors, "mean_fold_mae": float(np.mean(errors))})
    # Keep the settings with the lowest average error over the folds.
    best = min(candidates, key=lambda candidate: candidate["mean_fold_mae"])
    return best["settings"], candidates


def membership_record(data: AssayTables, indices: list[int]) -> dict:
    """Count the molecules and scaffolds in one set, for the report."""
    counts = Counter(data.scaffolds[i] for i in indices)
    return {"compounds": len(indices), "scaffolds": len(counts), "scaffold_counts": counts}


def evaluate(data: AssayTables, scheme: str) -> tuple[dict, dict, list[int]]:
    """Keep calibration and testing outside the same development-only model search.

    scheme: 'random' or 'scaffold'. Returns the report, the model artifact and the test row numbers.
    """
    # Step 1: assign each molecule (or scaffold group) to development, calibration or test, without using labels.
    indices = split_membership(data.identities, data.scaffolds, scheme, seed=SEED)
    development, calibration, test = (indices[role] for role in ("development", "calibration", "test"))
    X_dev = data.matrix[development]
    # Step 2: build three cross-validation folds inside the development set only.
    # The scaffold scheme uses GroupKFold, so a scaffold never sits on both sides of a fold.
    if scheme == "random":
        splitter = KFold(n_splits=3, shuffle=True, random_state=SEED).split(X_dev)
    else:
        groups = [data.scaffolds[i] for i in development]
        splitter = GroupKFold(n_splits=3).split(X_dev, groups=groups)
    folds = [([development[i] for i in train], [development[i] for i in hold]) for train, hold in splitter]
    graphs = [graph_arrays(Chem.MolFromSmiles(row["canonical_isomeric_smiles"])) for row in data.features]
    metrics, settings, estimators = {}, {}, {}
    held = calibration + test
    # The baseline predicts the development median for every held-out molecule.
    predictions = {"development_median": np.full(len(held), np.median(data.labels[development]))}
    # Step 3: tune each model with cross-validation, then refit it on all development rows.
    for name in (*MODEL_NAMES, "gnn"):
        selected, candidates = cross_validate(name, data, graphs, folds)
        estimators[name], predictions[name] = fit_predict(name, selected, data, graphs, development, held)
        settings[name] = {"selected": selected, "candidates": candidates}
    # The ensemble is the plain average of the three tabular models.
    predictions["ensemble"] = np.mean([predictions[name] for name in MODEL_NAMES], axis=0)
    n_calibration = len(calibration)
    # Step 4: score every model on the test molecules (the part of `held` after the calibration rows).
    for name, values in predictions.items():
        metrics[name] = regression_metrics(data.labels[test], values[n_calibration:])

    # Step 5: calibrate the interval on the calibration groups, then count how many test groups it covers.
    cal_groups = data.scaffolds if scheme == "scaffold" else data.identities
    ensemble = predictions["ensemble"]
    calibrated = calibration_width(abs(data.labels[calibration] - ensemble[:n_calibration]),
                                   [cal_groups[i] for i in calibration], coverage=NOMINAL_COVERAGE)
    half_width = calibrated["half_width"]
    test_covers = abs(data.labels[test] - ensemble[n_calibration:]) <= half_width
    group_covers = {key: all(test_covers[position] for position, index in enumerate(test)
                            if cal_groups[index] == key) for key in sorted({cal_groups[i] for i in test})}
    test_rows = []
    # Step 6: for each test molecule, record the closest development molecule and how similar it is.
    support = {data.identities[i]: data.features[i]["morgan_on_bits"] for i in development}
    for position, index in enumerate(test):
        closest, similarity = nearest_support(data.features[index]["morgan_on_bits"], support)
        test_rows.append({"identity": data.identities[index], "compound_id": data.features[index]["compound_id"],
                          "scaffold": data.scaffolds[index], "observed_pic50": float(data.labels[index]),
                          "predicted_pic50": {name: float(values[n_calibration + position])
                                               for name, values in predictions.items()},
                          "nearest_development": closest, "tanimoto_to_development": similarity,
                          "ensemble_in_interval": bool(test_covers[position])})
    dev_scaffolds, test_scaffolds = ({data.scaffolds[i] for i in group} for group in (development, test))
    # Record how many scaffolds are shared between the two sides of each fold (zero for the scaffold split).
    fold_records = [{"fit_rows": len(train), "check_rows": len(check),
                     "scaffold_overlap": len({data.scaffolds[i] for i in train} & {data.scaffolds[i] for i in check})}
                    for train, check in folds]
    report = {"scheme": scheme,
              "membership": {name: membership_record(data, members) for name, members in indices.items()},
              "membership_identities": {name: [data.identities[i] for i in members] for name, members in indices.items()},
              "development_test_scaffold_overlap": sorted(dev_scaffolds & test_scaffolds),
              "cross_validation_folds": fold_records, "settings": settings,
              "test_metrics": metrics, "test_predictions": test_rows,
              "ensemble_interval": {**calibrated, "empirical_molecule_coverage": float(test_covers.mean()),
                                    "molecules_covered": int(test_covers.sum()), "molecules_tested": len(test),
                                    "test_groups_all_covered": sum(group_covers.values()), "test_groups": len(group_covers)}}
    artifact = {"estimators": {name: estimators[name] for name in MODEL_NAMES},
                "training_fingerprints": support, "half_width": half_width}
    return report, artifact, test


def save_egfr(data: AssayTables, report: dict, artifact: dict, test: list[int], output: Path) -> None:
    """Save the unchanged scaffold-development ensemble for the next lesson.

    Writes the model file, three stored probe predictions and a manifest with fingerprints and library versions.
    """
    artifact["schema_version"] = 1
    artifact["target_assay"] = data.cohort["assay"]
    # Derive a support cutoff from development-only comparisons to a different scaffold.
    # For each training molecule: how similar is the closest training molecule with a different scaffold?
    support = artifact["training_fingerprints"]
    by_identity = dict(zip(data.identities, data.scaffolds))
    cross_scaffold_similarities = []
    for identity, fingerprint in support.items():
        alternatives = {key: bits for key, bits in support.items() if by_identity[key] != by_identity[identity]}
        cross_scaffold_similarities.append(nearest_support(fingerprint, alternatives)[1])
    # The 10th percentile of those similarities becomes the cutoff below which a query looks unfamiliar.
    support_cutoff = float(np.quantile(cross_scaffold_similarities, 0.10, method="lower"))
    artifact["applicability_min_tanimoto"] = support_cutoff
    model_path = output / "egfr_qsar_model.joblib"
    pending = model_path.with_suffix(".pending")
    joblib.dump(artifact, pending, compress=3)
    pending.replace(model_path)
    # Store three test molecules and their predictions, so a later reload can prove it reproduces them.
    probes = [data.features[i] for i in test[:3]]
    probes_path = output / "reload_probes.json"
    write_json(probes_path, {"features": probes, "predictions": [row["predicted_pic50"]["ensemble"]
                                                                for row in report["test_predictions"][:3]]})
    # The manifest records what the model is, how it was built and the fingerprints that guard it.
    manifest = {"schema_version": 1, "file": model_path.name, "model_sha256": digest(model_path),
                "target_id": data.cohort["target"], "target_assay": data.cohort["assay"],
                "variant": data.cohort["variant"], "endpoint": "pIC50", "components": list(MODEL_NAMES),
                "ensemble_rule": "arithmetic average of three tuned tabular models",
                "feature_recipe": {"morgan_bits": MORGAN_BITS, "radius": 2, "chirality": True,
                                   "maccs_bits": MACCS_BITS, "descriptors": list(DESCRIPTORS)},
                "rdkit_version": rdBase.rdkitVersion, "training_count": len(support),
                "all_measured_cohort_identities": data.identities,
                "applicability_min_tanimoto": support_cutoff,
                "applicability_rule": "10th percentile with lower interpolation of development leave-one-scaffold-out nearest Tanimoto",
                "interval_half_width": artifact["half_width"], "nominal_interval_coverage": NOMINAL_COVERAGE,
                "chapter_5_receipt_sha256": data.feature_receipt_sha256,
                "chapter_5_parquet_sha256": data.feature_parquet_sha256,
                "verification_file": probes_path.name, "verification_sha256": digest(probes_path),
                "versions": {name: version(name) for name in ("numpy", "scipy", "scikit-learn", "xgboost", "joblib", "rdkit")}}
    write_json(output / "MODEL_MANIFEST.json", manifest)


def main(inputs: Path, features: Path, output: Path) -> None:
    """Run the full lab for both targets and both split schemes."""
    output.mkdir(parents=True, exist_ok=True)
    for target in ("egfr", "kras_g12d"):
        data = load_tables(inputs, features, target)
        reports = {}
        print(f"{target}, {len(data.labels)} rows, {len(set(data.scaffolds))} exact scaffolds", flush=True)
        for scheme in ("random", "scaffold"):
            report, artifact, test = evaluate(data, scheme)
            reports[scheme] = report
            print(f"{target} {scheme}: test MAE {report['test_metrics']['ensemble']['mae']:.4f}", flush=True)
            # Only the EGFR scaffold-split ensemble is saved; Part 8 reloads it.
            if target == "egfr" and scheme == "scaffold":
                save_egfr(data, report, artifact, test, output)
        write_json(output / f"{target}_evaluation.json", {"cohort": data.cohort, "seed": SEED,
                   "input_shape": list(data.matrix.shape), "scaffold_counts": Counter(data.scaffolds),
                   "splits": reports})


if __name__ == "__main__":
    # Command line options let you point the script at other folders; the defaults match this repository.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "data/input")
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--output", type=Path, default=ROOT / "data/trained")
    args = parser.parse_args()
    main(args.inputs, args.features, args.output)
