"""Fetch the 16 public source files for Part 3 (UniProt, RCSB PDB and ChEMBL)
(Part 3: "Drug Discovery Targets and Molecular Identity")

A normal run of target_manifest_demo.py reads saved copies and never uses the internet. This script is the
one place that does. It downloads each file once, keeps its exact bytes, and writes the URL, time,
size and SHA-256 hash into research/download_receipts.json.

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Lists the 16 files and the public address each one comes from (SOURCES).
  2. Skips every file that already exists, after checking its hash against the receipt.
  3. Downloads each missing file with curl (HTTPS, certificate checking on, 45 second limit).
  4. Checks the download looks right: valid JSON, a FASTA file starting with ">", or an mmCIF file
     starting with "data_".
  5. Saves the file in data/raw/ and updates the receipt file after every download.

WHAT YOU NEED
  * Python 3.10 or newer, the curl program (expected at /usr/bin/curl) and internet access.
  * No account, key or paid service. This repository already contains all 16 files, so you only need
    this script to re-download them or to refresh the snapshot.

HOW TO RUN IT
  python code/fetch_sources.py
  With the files already present it prints "Preserved <name>" for each. To download fresh copies,
  move data/raw and research/download_receipts.json aside first. Databases change over time, so fresh
  copies can differ from the ones in the video; the receipt records the new hashes.
"""

# Standard library only: datetime for the download time, hashlib for hashes, subprocess to run curl.
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


# ROOT is the part folder (this file lives in code/, so go one level up).
ROOT = Path(__file__).resolve().parents[1]
# File name inside data/raw -> the public address it comes from.
SOURCES = {
    "uniprot-P00533.json": "https://rest.uniprot.org/uniprotkb/P00533.json",
    "uniprot-P01116.json": "https://rest.uniprot.org/uniprotkb/P01116.json",
    "uniprot-P01116-2.fasta": "https://rest.uniprot.org/uniprotkb/P01116-2.fasta",
    "rcsb-1M17-entry.json": "https://data.rcsb.org/rest/v1/core/entry/1M17",
    "rcsb-1M17-polymer.json": "https://data.rcsb.org/rest/v1/core/polymer_entity/1M17/1",
    "rcsb-7RPZ-entry.json": "https://data.rcsb.org/rest/v1/core/entry/7RPZ",
    "rcsb-7RPZ-polymer.json": "https://data.rcsb.org/rest/v1/core/polymer_entity/7RPZ/1",
    "rcsb-AQ4-chemcomp.json": "https://data.rcsb.org/rest/v1/core/chemcomp/AQ4",
    "rcsb-6IC-chemcomp.json": "https://data.rcsb.org/rest/v1/core/chemcomp/6IC",
    "rcsb-1M17.cif": "https://files.rcsb.org/download/1M17.cif",
    "rcsb-7RPZ.cif": "https://files.rcsb.org/download/7RPZ.cif",
    "chembl-CHEMBL553.json": "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL553.json",
    "chembl-mrtx1133-search.json": "https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?q=MRTX1133",
    "chembl-CHEMBL203-target.json": "https://www.ebi.ac.uk/chembl/api/data/target/CHEMBL203.json",
    "chembl-kras-target-search.json": "https://www.ebi.ac.uk/chembl/api/data/target.json?target_components__accession=P01116&limit=100",
    "chembl-status.json": "https://www.ebi.ac.uk/chembl/api/data/status.json",
}


def main() -> None:
    """Download any missing source files and keep the receipt file current."""
    # Make sure the folders for the data and the receipt exist.
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    receipts_path = ROOT / "research/download_receipts.json"
    receipts_path.parent.mkdir(parents=True, exist_ok=True)
    # Load earlier receipts so an existing file can be verified instead of replaced.
    previous = json.loads(receipts_path.read_text()) if receipts_path.exists() else []
    by_name = {row["file"]: row for row in previous}
    # Go through the files one at a time.
    for name, url in SOURCES.items():
        path = raw / name
        # A file that is already saved must match its receipt, otherwise stop: never overwrite evidence silently.
        if path.exists():
            blob = path.read_bytes()
            if name not in by_name or by_name[name]["sha256"] != hashlib.sha256(blob).hexdigest():
                raise ValueError(f"existing snapshot lacks a matching original receipt: {name}")
            print(f"Preserved {name}")
            continue
        # curl: fail on HTTP errors, follow redirects, quiet but show errors. Certificates are checked.
        completed = subprocess.run(
            ["/usr/bin/curl", "--fail", "--location", "--max-time", "45", "--silent", "--show-error", url],
            check=True, capture_output=True,
        )
        # The raw downloaded bytes; they are saved exactly as received.
        blob = completed.stdout
        # Sanity checks so an error page is never saved as if it were data.
        if name.endswith(".json"):
            json.loads(blob)
        elif name.endswith(".fasta") and not blob.startswith(b">"):
            raise ValueError(f"not FASTA: {name}")
        elif name.endswith(".cif") and not blob.lstrip().startswith(b"data_"):
            raise ValueError(f"not mmCIF: {name}")
        # Save the file, then record where it came from, when, how big and its SHA-256 hash.
        path.write_bytes(blob)
        by_name[name] = {
            "file": name, "path": f"data/raw/{name}", "url": url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "method": "public HTTPS via curl; TLS verification enabled",
        }
        receipts_path.write_text(json.dumps(list(by_name.values()), indent=2) + "\n")
        print(f"Retrieved {name}: {len(blob)} bytes")


if __name__ == "__main__":
    main()
