"""Fetch the public source files for Part 4 (ChEMBL records and background documents)
(Part 4: "Dose-Response Curves and IC50")

Ordinary runs of the lab and the curation script read saved copies and never touch the internet.
This script is the one place that does. It downloads each source file once, keeps its exact bytes,
and records the URL, time, size and SHA-256 hash in research/download_receipts.json.

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Lists every file the lesson needs (SOURCES), and the 12 activity IDs chosen for the lesson (SELECTED).
  2. If the ChEMBL activity file already exists, also adds the assay and document record of every
     selected activity.
  3. For each file that already exists, checks that its hash matches the receipt (a mismatch stops the run).
  4. Downloads only the missing files, four at a time, over HTTPS with certificate checking on.
  5. Checks each download looks right (valid JSON, a real PDF, or a page with the expected title).
  6. Saves the file and updates the receipt file.

WHAT YOU NEED
  * Python 3.10 or newer, the curl program, and internet access. No account, key or paid service.
  * The folder layout of this repository.

HOW TO RUN IT
  python code/fetch_sources.py
  The repository already contains the ChEMBL data files (data/raw). Running the script downloads
  the six background papers and web pages that are not stored here, which curate_activities.py needs.

WHAT YOU SHOULD SEE
  A line "Retrieved <path>: <n> bytes" for every file that was missing, then a "Preserved <n>
  snapshots" line. Web pages can change over time, so a newly downloaded page may have a different
  hash than the one in the video; the receipt is updated to the new hash.
"""

# Standard library only: a thread pool for parallel downloads, hashlib for hashes, subprocess to call curl.
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


# ROOT is the part folder (this file lives in code/, so go one level up).
ROOT = Path(__file__).resolve().parents[1]
# ChEMBL web-service query: every IC50 record for erlotinib (CHEMBL553) on EGFR (CHEMBL203), up to 1000 rows.
ACTIVITY_URL = "https://www.ebi.ac.uk/chembl/api/data/activity.json?molecule_chembl_id=CHEMBL553&target_chembl_id=CHEMBL203&standard_type=IC50&limit=1000"
# The 12 activity IDs chosen for the lesson. They are a teaching selection, not a complete or representative set.
SELECTED = (186628, 1682076, 1682080, 2194204, 2943654, 2943660,
            3261320, 3261330, 13446008, 13852013, 14586668, 14974603)
# File name inside the part folder -> where it comes from.
SOURCES = {
    "data/raw/chembl-egfr-erlotinib-ic50.json": ACTIVITY_URL,
    "data/raw/chembl-status.json": "https://www.ebi.ac.uk/chembl/api/data/status.json",
    "data/raw/chembl-CHEMBL553.json": "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL553.json",
    "data/raw/chembl-CHEMBL203.json": "https://www.ebi.ac.uk/chembl/api/data/target/CHEMBL203.json",
    "research/papers/hafner-2016-dash.pdf": "https://dash.harvard.edu/server/api/core/bitstreams/7312037e-02b3-6bd4-e053-0100007fdf3b/content",
    "research/sources/hafner-2016-pmc.html": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4887336/",
    "research/sources/chembl-data-questions.md": "https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/chembl-data-questions.md",
    "research/sources/chembl-general-questions.md": "https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/general-questions.md",
    "research/sources/assay-guidance-NBK91994.html": "https://www.ncbi.nlm.nih.gov/sites/books/NBK91994/",
    "research/papers/assay-guidance-NBK91994.pdf": "https://www.ncbi.nlm.nih.gov/sites/books/NBK91994/pdf/Bookshelf_NBK91994.pdf",
}


def acquire(item):
    """Download one source file, check it, save it, and return its receipt entry.

    `item` is a (relative file name, URL) pair. The checks depend on the file type: JSON must parse,
    a PDF must start with %PDF, and an HTML page must contain its expected title text.
    """
    name, url = item
    # curl: fail on HTTP errors, follow redirects, 45 second limit, quiet but show errors. Certificates are checked.
    completed = subprocess.run(["/usr/bin/curl", "--fail", "--location", "--max-time", "45", "--silent", "--show-error", url],
                               check=True, capture_output=True)
    # The raw downloaded bytes; they are saved exactly as received.
    blob = completed.stdout
    # Sanity checks so an error page is never saved as if it were data.
    if name.endswith(".json"):
        json.loads(blob)
    elif name.endswith(".pdf") and not blob.startswith(b"%PDF"):
        raise ValueError("not a PDF: " + name)
    elif name.endswith(".html") and not any(title in blob for title in [b"Growth rate inhibition", b"Assay Operations for SAR"]):
        raise ValueError("source HTML lacked its title: " + name)
    # Save the file, creating folders as needed.
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    # The receipt entry: where it came from, when, how big, and its SHA-256 hash.
    return {"path": name, "url": url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "method": "public HTTPS curl, TLS verification enabled; no account, paid endpoint or credentials"}


def main():
    """Work out which files are missing, download them in parallel, and keep the receipt file up to date."""
    # Load any existing receipts so earlier downloads are remembered.
    receipt = ROOT / "research/download_receipts.json"
    previous = json.loads(receipt.read_text()) if receipt.exists() else []
    known = {r["path"]: r for r in previous}
    sources = dict(SOURCES)
    # After the activity file exists, add the assay and document records of the selected activities.
    activities_path = ROOT / "data/raw/chembl-egfr-erlotinib-ic50.json"
    if activities_path.exists():
        all_rows = json.loads(activities_path.read_text())["activities"]
        rows = [r for r in all_rows if r["activity_id"] in SELECTED]
        for entity, key in [("assay", "assay_chembl_id"), ("document", "document_chembl_id")]:
            for identity in sorted({r[key] for r in rows}):
                sources[f"data/raw/chembl-{entity}-{identity}.json"] = f"https://www.ebi.ac.uk/chembl/api/data/{entity}/{identity}.json"
    # A file that already exists must match its receipt; a missing file is queued for download.
    todo = []
    for name, url in sources.items():
        path = ROOT / name
        if path.exists():
            if name not in known or hashlib.sha256(path.read_bytes()).hexdigest() != known[name]["sha256"]:
                raise ValueError("existing source lacks its matching receipt: " + name)
        else:
            todo.append((name, url))
    # Download up to four files at a time; write the receipt after each one so progress is never lost.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(acquire, todo):
            known[row["path"]] = row
            receipt.write_text(json.dumps(list(known.values()), indent=2) + "\n")
            print(f"Retrieved {row['path']}: {row['bytes']} bytes")
    # Summary line.
    print(f"Preserved {len(known)} snapshots; run again only to fetch selected assay/document context after first activity download.")


if __name__ == "__main__":
    main()
