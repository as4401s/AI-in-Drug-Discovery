"""Check the training run: partitions stay separate, outputs agree with the inputs, the model reloads, and a fresh replay matches.

What this file does
    * check re-reads the saved evaluation files and asserts that development, calibration and test sets never overlap,
      that scaffold folds never share a scaffold, that the chosen settings have the lowest cross-validation error,
      and that the saved model reloads and reproduces its stored predictions.
    * replay (with --repeat) runs train_models.py again into a temporary folder and compares the output bytes with the saved files.

What it needs
    The same libraries as train_models.py, and the files already written to data/trained/.

Run
    python code/verify_training.py            (fast checks)
    python code/verify_training.py --repeat   (also repeats every fit; takes a few minutes)

What to expect
    A JSON receipt. An AssertionError names the first check that failed.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from assay_tables import load_tables
from saved_model import open_model, verify_reload
from train_models import DEFAULT_FEATURES, ROOT


def read(path: Path) -> dict:
    """Read a JSON file into a dictionary."""
    return json.loads(path.read_text())


def check() -> dict:
    """Run every consistency check on the saved outputs and return the evidence as a dictionary."""
    output = ROOT / "data/trained"
    evidence = {}
    for target in ("egfr", "kras_g12d"):
        # Rebuild the inputs from the frozen files and compare them with what the evaluation file recorded.
        assay = load_tables(ROOT / "data/input", DEFAULT_FEATURES, target)
        results = read(output / f"{target}_evaluation.json")
        assert len(assay.identities) == results["input_shape"][0]
        assert assay.matrix.shape[1] == results["input_shape"][1]
        assert Counter(assay.scaffolds) == results["scaffold_counts"]
        keys = dict(zip(assay.identities, assay.scaffolds))
        for name, split in results["splits"].items():
            members = split["membership_identities"]
            development, calibration, test = (set(members[role]) for role in ("development", "calibration", "test"))
            # The three sets share no molecule, and together they cover every molecule exactly once.
            assert development.isdisjoint(calibration | test) and calibration.isdisjoint(test)
            assert development | calibration | test == set(assay.identities)
            assert {row["identity"] for row in split["test_predictions"]} == test
            if name == "scaffold":
                # In the scaffold split no scaffold appears in two sets, and no cross-validation fold shares one.
                a, b, c = ({keys[identity] for identity in role} for role in (development, calibration, test))
                assert a.isdisjoint(b | c) and b.isdisjoint(c)
                assert all(not fold["scaffold_overlap"] for fold in split["cross_validation_folds"])
            # The settings that were kept must be the candidates with the lowest mean cross-validation error.
            for candidate in split["settings"].values():
                assert min(candidate["candidates"], key=lambda option: option["mean_fold_mae"])["settings"] == candidate["selected"]
        evidence[target] = {"rows": len(keys), "scaffolds": len(set(keys.values())), "separate_partitions": True,
                            "scaffold_cross_validation_isolation": True}

    # The saved model must have been trained on exactly the development molecules of the scaffold split.
    manifest, ensemble = open_model(output / "MODEL_MANIFEST.json")
    development = read(output / "egfr_evaluation.json")["splits"]["scaffold"]["membership_identities"]["development"]
    assert set(ensemble["training_fingerprints"]) == set(development)
    evidence["reload"] = verify_reload(output / "MODEL_MANIFEST.json")
    evidence["saved_training_identity_count"] = manifest["training_count"]
    return evidence


def replay() -> dict:
    """Run training from inputs again without replacing the saved working artifact."""
    outputs = ROOT / "data/trained"
    files = ("egfr_evaluation.json", "kras_g12d_evaluation.json", "egfr_qsar_model.joblib", "MODEL_MANIFEST.json", "reload_probes.json")
    # Train into a temporary folder, then compare the new files with the saved ones byte for byte.
    with TemporaryDirectory(prefix="qsar-replay-") as directory:
        scratch = Path(directory)
        process = subprocess.run([sys.executable, "-B", str(ROOT / "code/train_models.py"), "--output", str(scratch)],
                                 text=True, capture_output=True, check=True)
        identical = {name: (scratch / name).read_bytes() == (outputs / name).read_bytes() for name in files}
        if not all(identical.values()):
            raise ValueError(f"A training replay differed: {identical}")
        return {"byte_identical": identical, "mlp_max_iteration_warnings": process.stderr.count("ConvergenceWarning:"),
                "run_output": process.stdout.splitlines()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", action="store_true", help="rerun every fit and compare artifact bytes")
    arguments = parser.parse_args()
    receipt = check()
    if arguments.repeat:
        receipt["training_replay"] = replay()
    print(json.dumps(receipt, indent=2, allow_nan=False))
