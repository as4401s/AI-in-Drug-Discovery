"""Reload the saved EGFR ensemble safely and predict potency, an interval and structural support for new molecules.

What this file does
    * open_model checks the model file's SHA-256 fingerprint and the library versions, then loads it.
    * predict_features averages the three tabular models and adds the calibrated interval and the nearest training structure.
    * verify_reload predicts a few stored probe molecules in a fresh process and checks the numbers agree to 1e-10.

What it needs
    Python 3.10 or newer with the same library versions that built the model (the manifest lists them): NumPy, scikit-learn, XGBoost, joblib and RDKit.

What to expect
    Run: python code/saved_model.py data/trained/MODEL_MANIFEST.json
    It prints a JSON report with the maximum prediction difference, which should be 0 or within 1e-10.

Safety note
    joblib files can run code when they are loaded. Load only a model you built yourself or whose fingerprint you verified, as this file does.
"""

import argparse
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from assay_tables import require_digest
from model_inputs import make_matrix, nearest_support


def open_model(manifest_file: Path) -> tuple[dict, dict]:
    """Load the trusted course model only after verifying its exact bytes and versions.

    manifest_file: MODEL_MANIFEST.json, which records the model's fingerprint and the versions that built it.
    Returns the manifest and the loaded model dictionary.
    """
    manifest = json.loads(manifest_file.read_text())
    expected_name = "egfr_qsar_model.joblib"
    if manifest["schema_version"] != 1 or manifest["file"] != expected_name:
        raise ValueError("Expected the Chapter 7 EGFR model manifest")
    # A model saved with other library versions could behave differently, so the versions must match.
    for package, expected_version in manifest["versions"].items():
        if version(package) != expected_version:
            raise ValueError(f"The saved model expects {package} {expected_version}")
    data = (manifest_file.parent / expected_name).read_bytes()
    # Compare the file's fingerprint with the one recorded when the model was saved.
    if sha256(data).hexdigest() != manifest["model_sha256"]:
        raise ValueError("The saved model SHA-256 differs from its manifest")
    # Joblib can execute code when loading. Use this only for the locally built trusted artifact.
    artifact = joblib.load(BytesIO(data))
    # The loaded object has to agree with the manifest on every property it records.
    if (artifact["schema_version"] != manifest["schema_version"]
            or artifact["target_assay"] != manifest["target_assay"]
            or list(artifact["estimators"]) != manifest["components"]
            or artifact["half_width"] != manifest["interval_half_width"]
            or artifact["applicability_min_tanimoto"] != manifest["applicability_min_tanimoto"]
            or len(artifact["training_fingerprints"]) != manifest["training_count"]):
        raise ValueError("Model properties differ from the Chapter 7 manifest")
    return manifest, artifact


def predict_features(artifact: dict, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return potency, calibrated bounds and the nearest observed training structure.

    artifact: the loaded model. rows: Part 5 feature rows (structure columns only).
    """
    if not rows:
        return []
    # Same recipe as training: expand the fingerprint bits and descriptors into one number row per molecule.
    matrix = make_matrix(rows)
    # The ensemble prediction is the plain average of the three tuned models.
    estimates = np.mean([model.predict(matrix) for model in artifact["estimators"].values()], axis=0)
    support = artifact["training_fingerprints"]
    if not np.isfinite(estimates).all():
        raise ValueError("Model predictions must be finite")
    output = []
    for row, prediction in zip(rows, estimates):
        # Support check: how similar is the closest training molecule? A low value means an unfamiliar structure.
        closest, similarity = nearest_support(row["morgan_on_bits"], support)
        estimate = float(prediction)
        width = artifact["half_width"]
        output.append({"compound_id": row["compound_id"], "identity": row["standard_inchi_key"],
                       "predicted_pic50": estimate, "interval_lower_pic50": estimate - width,
                       "interval_upper_pic50": estimate + width, "nearest_training_identity": closest,
                       "nearest_training_tanimoto": similarity,
                       "passes_applicability": similarity >= artifact["applicability_min_tanimoto"]})
    return output


def verify_reload(manifest_file: Path) -> dict:
    """Compare separate-process inference with the original in-memory fitted evaluator."""
    manifest, model = open_model(manifest_file)
    # The probe file stores three molecules and the predictions the model made right after training.
    probes_file = require_digest(manifest_file.parent / manifest["verification_file"],
                                 manifest["verification_sha256"])
    probes = json.loads(probes_file.read_text())
    predicted = predict_features(model, probes["features"])
    values = [row["predicted_pic50"] for row in predicted]
    # A reloaded model must reproduce the stored predictions to within 1e-10.
    np.testing.assert_allclose(values, probes["predictions"], rtol=0, atol=1e-10)
    difference = max(abs(current - reference) for current, reference in zip(values, probes["predictions"]))
    return {"model_sha256": manifest["model_sha256"], "probe_count": len(values),
            "max_absolute_prediction_difference": difference, "outputs": predicted}


if __name__ == "__main__":
    # Command line: pass the path of MODEL_MANIFEST.json and read the JSON report.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_reload(args.manifest), indent=2, allow_nan=False))
