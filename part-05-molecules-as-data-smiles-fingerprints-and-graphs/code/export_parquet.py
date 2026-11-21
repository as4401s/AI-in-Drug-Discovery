"""Write the typed Part 5 feature tables (Parquet files) that the Part 7 training lab reads.

What this file does
    1. Calls feature_handoff.export to regenerate the feature rows with the RDKit installed on your computer.
    2. Writes each cohort as a typed, compressed Parquet table (column names and number types are fixed by SCHEMA).
    3. Reads every table back and checks that each value is unchanged, then records the SHA-256 fingerprint of each Parquet file
       in PARQUET_RECEIPT.json.

Why Parquet
    A Parquet table keeps column types (text, whole numbers, decimals, lists of bit positions), so the training lab reads exactly
    the numbers that were written, and the receipt lets it verify the file before use.

What it needs
    Python 3.10 or newer, RDKit and PyArrow.

Run
    python code/export_parquet.py <folder with COHORT_LOCK.json> <destination folder>

What to expect
    egfr_features.parquet, kras_g12d_features.parquet, a feature_rows/ folder and PARQUET_RECEIPT.json in the destination.
"""

import argparse
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from feature_handoff import export, json_bytes, sha

# The column names and types of the feature table. Counts are small whole numbers; bit positions are lists of whole numbers.
SCHEMA = pa.schema([
    ("compound_id", pa.string()), ("canonical_isomeric_smiles", pa.string()),
    ("standard_inchi_key", pa.string()), ("formula", pa.string()),
    ("MolWt", pa.float64()), ("MolLogP", pa.float64()), ("TPSA", pa.float64()),
    ("HBD", pa.int16()), ("HBA", pa.int16()), ("heavy_atoms", pa.int16()),
    ("rotatable_bonds", pa.int16()), ("num_components", pa.int16()),
    ("unassigned_tetrahedral_centers", pa.int16()),
    ("morgan_on_bits", pa.list_(pa.int16())), ("maccs_on_bits", pa.list_(pa.int16())),
])


def export_tables(input_dir: Path, destination: Path) -> None:
    """Regenerate the features with this runtime and round-trip every Parquet value."""
    destination.mkdir(parents=True, exist_ok=True)
    source = destination / "feature_rows"
    # First write the JSON feature rows and their receipt (the Part 5 handoff).
    export(input_dir, source)
    receipt = json.loads((source / "FEATURE_RECEIPT.json").read_text())
    receipt["pyarrow_version"] = pa.__version__
    for cohort, entry in receipt["cohorts"].items():
        rows = json.loads((source / entry["feature_file"]).read_text())
        # Build a typed table from the rows and save it with zstd compression.
        table = pa.Table.from_pylist(rows, schema=SCHEMA)
        path = destination / f"{cohort}_features.parquet"
        pq.write_table(table, path, compression="zstd", version="2.6")
        # Read the file back: every value must equal the value that was written.
        if pq.read_table(path).to_pylist() != rows:
            raise ValueError(f"{cohort}: values changed during the Parquet round trip")
        entry.update(parquet=path.name, parquet_sha256=sha(path))
    (destination / "PARQUET_RECEIPT.json").write_bytes(json_bytes(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    export_tables(args.input_dir, args.destination)
