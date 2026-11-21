"""Load the stamped Part 5 feature table, join it to the measurements, and add exact Bemis-Murcko scaffold keys.

What this file does
    * require_digest refuses to read a file whose SHA-256 fingerprint differs from the recorded one.
    * scaffold_key reduces a molecule to its ring-and-linker core with RDKit's Murcko function.
    * load_tables checks the receipts, reads the Parquet feature table and the measured labels, and returns one AssayTables object.

What it needs
    Python 3.10 or newer, NumPy, RDKit and PyArrow. The Part 5 handoff folder holds the Parquet files and their receipt.

What to expect
    For EGFR: 170 molecules, each with an identity, a scaffold, a feature row and a measured pIC50.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from rdkit import Chem, rdBase
from rdkit.Chem.Scaffolds import MurckoScaffold

from model_inputs import make_matrix, match_labels


def digest(path: Path) -> str:
    """Return the SHA-256 fingerprint of a file's bytes (a short text that changes if any byte changes)."""
    return sha256(path.read_bytes()).hexdigest()


def require_digest(path: Path, expected: str) -> Path:
    """Return the path only if the file matches the recorded fingerprint; otherwise stop with an error."""
    if digest(path) != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")
    return path


def scaffold_key(smiles: str) -> str:
    """Group ring-and-linker SMILES; keep acyclic structures in a shared group.

    The Bemis-Murcko scaffold keeps the rings and the chains that link them and removes the side groups.
    """
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Invalid structure: {smiles}")
    # includeChirality=False means mirror images share one scaffold.
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=molecule, includeChirality=False)
    # A molecule without rings has an empty scaffold, so it joins one shared group.
    return scaffold or "[acyclic]"


@dataclass(frozen=True)
class AssayTables:
    """Everything the models need for one target, kept together so the rows can never drift apart."""

    features: list[dict[str, Any]]
    labels: np.ndarray
    matrix: np.ndarray
    identities: list[str]
    scaffolds: list[str]
    cohort: dict[str, Any]
    feature_receipt_sha256: str
    feature_parquet_sha256: str


def load_tables(inputs: Path, chapter_five: Path, target: str) -> AssayTables:
    """Verify both data receipts before joining on one compound identity per row.

    inputs: folder with the frozen activity cohorts. chapter_five: the Part 5 Parquet handoff folder.
    target: 'egfr' or 'kras_g12d'.
    """
    # The Part 5 receipt records which RDKit version and which files produced the features.
    receipt = chapter_five / "PARQUET_RECEIPT.json"
    provenance = json.loads(receipt.read_text())
    if provenance["rdkit_version"] != rdBase.rdkitVersion:
        raise ValueError("The Chapter 5 chemistry version and training runtime differ")
    # The cohort lock must be exactly the one the feature table was built from.
    lock = require_digest(inputs / "COHORT_LOCK.json", provenance["cohort_lock_sha256"])
    cohort = json.loads(lock.read_text())["target_cohorts"][target]
    export = provenance["cohorts"][target]
    expected_labels = cohort["sha256"]["labels.json"]
    if export["label_file_sha256"] != expected_labels:
        raise ValueError("Feature receipt and activity cohort require different labels")
    # Verify the labels file and the feature table against their recorded fingerprints before reading them.
    labels_file = require_digest(inputs / target / "labels.json", expected_labels)
    feature_path = require_digest(chapter_five / export["parquet"], export["parquet_sha256"])
    features = pq.read_table(feature_path).to_pylist()
    label_rows = json.loads(labels_file.read_text())
    # The feature table must hold structure-only columns: a pic50 column here would leak the answer.
    if len(features) != cohort["curated_identities"] or "pic50" in features[0]:
        raise ValueError("Expected one structure-only feature row per locked identity")

    # One identity and one scaffold per molecule, then the number table X and the measurement vector y.
    identities = [row["standard_inchi_key"] for row in features]
    scaffolds = [scaffold_key(row["canonical_isomeric_smiles"]) for row in features]
    return AssayTables(features, match_labels(features, label_rows), make_matrix(features),
                       identities, scaffolds, cohort, digest(receipt), digest(feature_path))
