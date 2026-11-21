"""Hand the Part 5 structure features to the Part 7 training lab: one feature row per molecule, with a receipt that proves where it came from.

What this file does
    * feature_rows turns each structure (SMILES plus its InChIKey) into one row of descriptors, Morgan on-bits and MACCS on-bits,
      using the same functions as molecular_representation_lab.py. It checks the identity of every molecule on the way.
    * export reads a locked activity cohort, calls feature_rows for each target and writes the rows and a FEATURE_RECEIPT.json
      that records the SHA-256 fingerprint of every input and output file.

The handoff contract
    The feature rows contain structure information only. The measured pIC50 stays in a separate file and is joined later by
    the InChIKey, so a model can never see its own answer in its inputs.

What it needs
    Python 3.10 or newer and RDKit. molecular_representation_lab.py must sit in the same folder.

Run
    python code/feature_handoff.py <folder with COHORT_LOCK.json> <output folder>

What to expect
    For each target one *_feature_rows.json file (EGFR: 170 rows, KRAS G12D: 23 rows) and one FEATURE_RECEIPT.json.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from rdkit import rdBase

# The representation functions live next to this file, in molecular_representation_lab.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from molecular_representation_lab import (  # noqa: E402
    MORGAN_SETTINGS, describe, generator, json_bytes, maccs_bundle, parse_input, sha,
)


def feature_rows(structures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Emit descriptor and fingerprint columns keyed to unique compound structures.

    structures: dictionaries with 'compound_id', 'smiles' and 'inchikey'. Returns one feature row per structure,
    sorted by InChIKey, with no measurement column.
    """
    # Each structure must appear once; a repeated InChIKey means the same molecule is listed twice.
    keys = {row["inchikey"] for row in structures}
    if len(keys) != len(structures):
        raise ValueError("Structure input repeats a standard InChIKey")

    # One Morgan fingerprint generator, built once with the radius, size and chirality settings of Part 5.
    morgan = generator()
    features = []
    # Sorting by InChIKey makes the output order the same on every run.
    for row in sorted(structures, key=lambda entry: entry["inchikey"]):
        compound_id = row["compound_id"]
        # Parse and sanitize the SMILES with the Part 5 checks; stop if the structure is rejected.
        audit, molecule = parse_input({"input_id": compound_id, "smiles": row["smiles"]})
        if molecule is None:
            raise ValueError(f"{compound_id}: {audit['reason']}")
        # Descriptors, formula, InChIKey and the other identity columns of Part 5.
        properties = describe(molecule)
        # The structure we parsed must be the one named in the activity record.
        if properties["standard_inchi_key"] != row["inchikey"]:
            raise ValueError(f"{compound_id}: the molecular identity differs from the activity record")
        if properties["num_components"] != 1:
            raise ValueError(f"{compound_id}: the feature input needs one connected structure")

        features.append({
            "compound_id": compound_id,
            **properties,
            # Store each fingerprint as the list of positions that are switched on.
            "morgan_on_bits": list(morgan.GetFingerprint(molecule).GetOnBits()),
            "maccs_on_bits": maccs_bundle(molecule)["on_bits"],
        })
    return features


def export(input_dir: Path, output_dir: Path) -> None:
    """Check the source receipt and retain the exact inputs and output digests.

    input_dir: folder with COHORT_LOCK.json and one sub-folder per target. output_dir: where the rows and the receipt go.
    """
    lock_path = input_dir / "COHORT_LOCK.json"
    lock = json.loads(lock_path.read_text())
    # The receipt starts with who produced the features and with which settings and RDKit version.
    receipt = {
        "schema_version": 1,
        "feature_source": "AI in Drug Discovery Chapter 5 molecular_representation_lab.py",
        "cohort_lock_sha256": sha(lock_path),
        "chembl_release": lock["release"],
        "rdkit_version": rdBase.rdkitVersion,
        "morgan": MORGAN_SETTINGS,
        "maccs_storage_bits": 167,
        "cohorts": {},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, cohort in lock["target_cohorts"].items():
        label_path = input_dir / name / "labels.json"
        labels_sha = sha(label_path)
        # The labels file has to be exactly the one recorded in the cohort lock.
        if labels_sha != cohort["sha256"]["labels.json"]:
            raise ValueError(f"{name}: activity input differs from the cohort lock")
        rows = feature_rows(json.loads(label_path.read_text()))
        if len(rows) != cohort["curated_identities"]:
            raise ValueError(f"{name}: feature count differs from the cohort lock")
        output = output_dir / f"{name}_feature_rows.json"
        output.write_bytes(json_bytes(rows))
        # Record the row count and the fingerprints of the label file and the feature file.
        receipt["cohorts"][name] = {
            "rows": len(rows), "label_file_sha256": labels_sha,
            "feature_file": output.name, "feature_file_sha256": sha(output),
        }
    (output_dir / "FEATURE_RECEIPT.json").write_bytes(json_bytes(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="directory containing the ChEMBL cohort lock")
    parser.add_argument("output_dir", type=Path, help="destination for feature rows and their receipt")
    arguments = parser.parse_args()
    export(arguments.input_dir, arguments.output_dir)
