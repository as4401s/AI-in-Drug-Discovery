"""Curate a deliberately small panel of REAL measured records, without pooling assays
(Part 4: "Dose-Response Curves and IC50")

The lab script (dose_response_lab.py) fits made-up wells. This script is its counterpart for real
data: twelve hand-picked ChEMBL records for erlotinib (CHEMBL553) against EGFR (CHEMBL203), each
checked for what it really measured before anyone is allowed to call it a label.

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Re-checks the SHA-256 hash and size of every saved source file listed in
     research/download_receipts.json, so the frozen inputs cannot change silently.
  2. Confirms the exact compound (CHEMBL553, InChIKey AAKJLRGGTJKAMG-UHFFFAOYSA-N) and the exact target
     (human EGFR, UniProt P00533) against the Part 3 result.
  3. Joins each selected activity record to its assay and its source paper (document) and checks
     that the three agree.
  4. Applies written-down rules (see classify) and gives every record a status such as
     retained_individual_assay_only, excluded_censored, excluded_missing, excluded_unknown_variant,
     excluded_context, excluded_duplicate, excluded_variant or excluded_target_confidence.
  5. Computes pIC50 only for exact ("=") values and cross-checks it against ChEMBL's pChEMBL value.
  6. Writes data/outputs/measured_activity_curation.json and .csv plus a run receipt.

WHAT YOU NEED
  * Python 3.10 or newer, the sibling files dose_response_lab.py and fetch_sources.py, and the saved
    data in data/raw. No network is used by THIS script.
  * Six background documents (two papers and four web pages, listed in fetch_sources.py) are
    hash-checked too. They are not stored in this repository. Run  python code/fetch_sources.py  once
    (needs internet) and it downloads them.

HOW TO RUN IT
  python code/fetch_sources.py            (once, to fetch the six background documents)
  python code/curate_activities.py
  python -m unittest discover -s code -p "test_curate_activities.py"

WHAT YOU SHOULD SEE (values from the run shown in the video)
  209 source rows were acquired, 12 were selected, and exactly ONE is retained:
    retained_individual_assay_only ..... 1   (activity 13852013, IC50 = 2.6 nM, confidence score 9)
    excluded_censored .................. 2   (a "> 1000" bound is not an exact IC50)
    excluded_context ................... 2   (cell-based phosphorylation, not a biochemical assay)
    excluded_duplicate ................. 2
    excluded_unknown_variant ........... 2
    excluded_missing ................... 1   (never imputed as zero)
    excluded_variant ................... 1   (T790M mutant)
    excluded_target_confidence ......... 1
  pooled assays: 0 (no averages, no ranking across assays)

HOW TO READ THE RESULT
  A database value is a label only after you know the molecule, target, variant, assay format,
  relation and units. Most of these records are not interchangeable, so none are pooled.
"""

# Standard library imports: Counter counts statuses, csv/json write the outputs, math checks numbers, platform/time fill the receipt.
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import time

# Reuse helpers from the other script: the part folder, stable JSON bytes, pIC50, file hash and the Part 3 identity check.
from dose_response_lab import ROOT, json_bytes, pic50, sha, validate_prerequisite
# SELECTED is the list of the 12 ChEMBL activity IDs chosen for this lesson.
from fetch_sources import SELECTED


# Manual scientific annotations are tied to the frozen source descriptions.
# Null mutation fields do not prove wild type: use explicit assay wording only.
# One tuple per record: (variant, endpoint context, cell line, exposure minutes). 'unknown' means the source does not say.
ANNOTATIONS = {
    186628: ("unknown", "biochemical", None, None),
    1682076: ("unknown", "cellular_phosphorylation", "NIH3T3", None),
    1682080: ("unknown", "biochemical_fusion_protein", None, None),
    2194204: ("unknown", "biochemical", None, None),
    2943654: ("unknown", "biochemical", None, None),
    2943660: ("T790M", "biochemical", None, None),
    3261320: ("L858R", "biochemical", None, None),
    3261330: ("reference_explicit_wild_type", "biochemical", None, None),
    13446008: ("reference_explicit_wild_type", "cellular_phosphorylation", "LoVo", 120),
    13852013: ("reference_explicit_wild_type", "biochemical", None, 60),
    14586668: ("reference_explicit_wild_type", "biochemical", None, 60),
    14974603: ("reference_explicit_wild_type", "biochemical", None, None),
}


def classify(row, assay, variant, endpoint):
    """Decide whether one activity record can be kept, and write down every reason.

    Arguments
      row      the ChEMBL activity record
      assay    the matching ChEMBL assay record (its confidence score is used)
      variant  our reading of the EGFR variant: "unknown", "reference_explicit_wild_type", or a mutation
      endpoint what the assay measured, e.g. "biochemical" or "cellular_phosphorylation"
    Returns (status, reasons): a status word and the list of plain-language reasons. The checks run in a
    fixed order, and the last matching rule wins for the status; every reason found is still listed.
    """
    # Collect every reason a record has a problem, so nothing is hidden behind a single label.
    reasons = []
    # Wrong compound or wrong target: stop treating it as erlotinib on EGFR.
    if row["molecule_chembl_id"] != "CHEMBL553" or row["target_chembl_id"] != "CHEMBL203":
        reasons.append("wrong molecule or target identity")
    # Only IC50 in nanomolar is compatible with this lesson's endpoint.
    if row["standard_type"] != "IC50" or row["standard_units"] not in ("nM", None):
        reasons.append("incompatible endpoint or units")
    # ChEMBL confidence 9 = direct single-protein target assignment; anything else is weaker.
    if assay["confidence_score"] != 9:
        reasons.append("assay-to-target assignment is not direct single protein confidence 9")
    # No number means no label. A missing value is never replaced by zero.
    if row["standard_value"] is None or row["standard_relation"] is None:
        reasons.append("missing numeric measurement/relation; never impute zero")
        status = "excluded_missing"
    # A bound such as '> 1000' says the IC50 is above that number; it is not an exact IC50.
    elif row["standard_relation"] != "=":
        reasons.append("censored bound, not an exact IC50; retain relation and no point pIC50")
        status = "excluded_censored"
    # A cell-based result measures something different from a biochemical enzyme assay.
    elif endpoint.startswith("cellular"):
        reasons.append("cellular phosphorylation context differs from biochemical reference panel")
        status = "excluded_context"
    # An explicit mutant (e.g. T790M) is not the reference EGFR of Part 3.
    elif variant not in ("unknown", "reference_explicit_wild_type"):
        reasons.append("explicit mutant differs from guided reference EGFR")
        status = "excluded_variant"
    # ChEMBL flags records that may repeat one another; repeats are not independent confirmation.
    elif row["potential_duplicate"]:
        reasons.append("ChEMBL potential_duplicate flag; not independent replication")
        status = "excluded_duplicate"
    # A missing mutation field is not proof of wild type, so unknown variants are not retained.
    elif variant == "unknown":
        reasons.append("variant unknown; null mutation metadata is not proof of reference sequence")
        status = "excluded_unknown_variant"
    else:
        # Everything passed. The record is kept, but only inside its own assay, never pooled.
        status = "retained_individual_assay_only" if assay["confidence_score"] == 9 else "excluded_target_confidence"
    # Identity and endpoint failures override every other status.
    if row["molecule_chembl_id"] != "CHEMBL553" or row["target_chembl_id"] != "CHEMBL203" or row["standard_type"] != "IC50" or row["standard_units"] not in ("nM", None):
        status = "excluded_identity_or_endpoint"
    # ChEMBL's own data-validity warnings also exclude a record.
    if row.get("data_validity_comment") not in (None, "Manually validated"):
        reasons.append("ChEMBL data validity flag: " + row["data_validity_comment"])
        status = "excluded_validity"
    # A zero, negative or non-finite concentration cannot be a valid potency label.
    if row["standard_value"] is not None and (not math.isfinite(float(row["standard_value"])) or float(row["standard_value"]) <= 0):
        reasons.append("nonpositive or nonfinite concentration is not a valid exact potency label")
        status = "excluded_invalid_value"
    # Mention an explicit mutant even when another rule decided the status first.
    if variant not in ("unknown", "reference_explicit_wild_type") and status != "excluded_variant":
        reasons.append("also explicit nonreference variant " + variant)
    # Always remind the reader: the exact protein construct and ATP level are not recorded here.
    reasons.append("construct sequence/ATP concentration not fully specified in retained assay record; no exact 1M17-construct match inferred")
    return status, reasons


def build_table(root: Path = ROOT):
    """Read the frozen inputs, run every check, and return the curation table plus its counts and limits.

    Nothing is downloaded here. Any failed identity, join or consistency check raises ValueError, so a
    broken input stops the run instead of producing a plausible-looking table.
    """
    # Step 1: verify the frozen source snapshots.
    raw = root / "data/raw"
    # The receipt file lists every downloaded file with its URL, size and SHA-256 hash.
    receipts = json.loads((root / "research/download_receipts.json").read_text())
    for receipt in receipts:
        path = root / receipt["path"]
        if sha(path) != receipt["sha256"] or path.stat().st_size != receipt["bytes"]:
            raise ValueError("source snapshot failed its retained identity: " + receipt["path"])
    # Step 2: check identity against the Part 3 result, its saved hash, the compound and the target.
    manifest = json.loads((raw / "episode03-target_reference_manifest.v1.json").read_text())
    validate_prerequisite(manifest)
    prerequisite_identity = json.loads((raw / "PREREQUISITE_IDENTITY.json").read_text())
    if sha(raw / "episode03-target_reference_manifest.v1.json") != prerequisite_identity["sha256"]:
        raise ValueError("episode 3 prerequisite snapshot identity differs")
    molecule = json.loads((raw / "chembl-CHEMBL553.json").read_text())
    if molecule["molecule_structures"]["standard_inchi_key"] != "AAKJLRGGTJKAMG-UHFFFAOYSA-N":
        raise ValueError("molecule no longer matches the exact episode 3 reference")
    target = json.loads((raw / "chembl-CHEMBL203.json").read_text())
    if target["organism"] != "Homo sapiens" or [c["accession"] for c in target["target_components"]] != ["P00533"]:
        raise ValueError("target identity no longer matches human EGFR P00533")
    # Step 3: load the frozen activity response and make sure it is complete (not a truncated page).
    activity = json.loads((raw / "chembl-egfr-erlotinib-ic50.json").read_text())
    if activity["page_meta"]["next"] is not None or len(activity["activities"]) != activity["page_meta"]["total_count"]:
        raise ValueError("activity acquisition is truncated")
    # Index the activities by ID so the selected ones can be looked up.
    by_id = {r["activity_id"]: r for r in activity["activities"]}
    if not set(SELECTED) <= set(by_id):
        raise ValueError("selected activity missing from frozen response")
    # Step 4: build one curated row per selected activity.
    rows = []
    for identity in SELECTED:
        row = by_id[identity]
        # Load the assay and document records for this activity.
        assay = json.loads((raw / f"chembl-assay-{row['assay_chembl_id']}.json").read_text())
        document = json.loads((raw / f"chembl-document-{row['document_chembl_id']}.json").read_text())
        # The activity, the assay and the document must all describe the same experiment.
        if (assay["assay_chembl_id"], assay["target_chembl_id"], assay["document_chembl_id"], assay["description"]) != (row["assay_chembl_id"], row["target_chembl_id"], row["document_chembl_id"], row["assay_description"]):
            raise ValueError("assay/activity/document join disagrees")
        # Look up our written annotation for this record.
        variant, endpoint, cell, duration = ANNOTATIONS[identity]
        # A 'wild type' annotation is only allowed if the assay text really says wild type.
        if variant == "reference_explicit_wild_type" and "wild type" not in row["assay_description"].lower():
            raise ValueError("wild type annotation is unsupported by the frozen assay wording")
        # A mutant annotation must agree with ChEMBL's own variant field.
        if variant not in ("unknown", "reference_explicit_wild_type") and row["assay_variant_mutation"] != variant:
            raise ValueError("mutant annotation disagrees with the explicit source field")
        # Apply the written rules.
        status, reasons = classify(row, assay, variant, endpoint)
        # Convert the stored number to a float (None stays None).
        value = float(row["standard_value"]) if row["standard_value"] is not None else None
        # pIC50 only for exact '=' values; bounds get none.
        exact_pic50 = pic50(value) if value is not None and value > 0 and row["standard_relation"] == "=" else None
        # Cross-check against ChEMBL's rounded pChEMBL value (tolerance 0.011).
        if exact_pic50 is not None and row["pchembl_value"] is not None and abs(exact_pic50 - float(row["pchembl_value"])) > 0.011:
            raise ValueError("local molar conversion disagrees with reported rounded pChEMBL")
        # The curated row keeps both the ChEMBL standardized fields and the published values, plus provenance links.
        rows.append({
            "activity_id": identity, "molecule_chembl_id": row["molecule_chembl_id"],
            "standard_inchi_key": molecule["molecule_structures"]["standard_inchi_key"],
            "canonical_smiles": molecule["molecule_structures"]["canonical_smiles"],
            "target_chembl_id": row["target_chembl_id"], "uniprot_accession": "P00533",
            "target_organism": row["target_organism"], "assay_chembl_id": row["assay_chembl_id"],
            "assay_type": row["assay_type"], "bao_format": row["bao_format"], "bao_label": row["bao_label"],
            "confidence_score": assay["confidence_score"], "confidence_description": assay["confidence_description"],
            "variant": variant, "variant_source": "explicit assay description/variant fields; unknown retained where unspecified",
            "assay_variant_mutation_original": row["assay_variant_mutation"], "endpoint_context": endpoint,
            "cell_line": cell, "exposure_minutes": duration, "ATP_concentration": None,
            "substrate_description": "poly (Glu, Tyr) 4:1" if identity in (13852013, 14586668) else None,
            "substrate_concentration": None,
            "construct_sequence": None, "assay_description": row["assay_description"],
            "standard_type": row["standard_type"], "standard_relation": row["standard_relation"],
            "standard_value": value, "standard_units": row["standard_units"],
            "published_type": row["type"], "published_relation": row["relation"],
            "published_value": row["value"], "published_units": row["units"],
            "pIC50_exact_point": exact_pic50, "pchembl_value_original": row["pchembl_value"],
            "potential_duplicate": row["potential_duplicate"], "data_validity_comment": row["data_validity_comment"],
            "activity_comment": row["activity_comment"], "document_chembl_id": row["document_chembl_id"],
            "document_doi": document.get("doi"), "document_title": document.get("title"),
            "document_year": document.get("year"), "curation_status": status,
            "reasons": " | ".join(reasons), "pooling_group": "single-assay:" + row["assay_chembl_id"] if status == "retained_individual_assay_only" else None,
            "measured_versus_predicted": "literature measurement as curated by ChEMBL; not independently remeasured or refitted here",
            "source_activity_url": f"https://www.ebi.ac.uk/chembl/api/data/activity/{identity}.json",
            "source_assay_url": f"https://www.ebi.ac.uk/chembl/api/data/assay/{row['assay_chembl_id']}.json",
            "source_license": "CC BY-SA 3.0; ChEMBL/EMBL-EBI; preserve release attribution and share-alike data terms",
        })
    # Step 5: record which ChEMBL release the snapshot came from, then return the table.
    release = json.loads((raw / "chembl-status.json").read_text())
    return {"artifact_id": "wb.add.episode04.measured-activity-curation.v1", "schema_version": "1.0.0",
            "producer_episode": 4, "chembl_status": release, "acquired_source_row_count": len(by_id),
            "selection": "12 deliberately selected teaching cases, not exhaustive or representative; no averages/rankings across assays",
            "counts": dict(Counter(r["curation_status"] for r in rows)), "rows": rows,
            "limits": ["ChEMBL confidence 9 concerns assay-to-target mapping, not experimental quality or clinical validity",
                       "Assay B/F labels alone do not distinguish all cellular contexts; inspect descriptions and BAO",
                       "Reference wording is not a verified exact full sequence/isoform/construct match",
                       "Retained rows stay in separate assay partitions; no common IC50, mean or synthetic-data join is computed",
                       "Original article methods were not independently reanalyzed for these database records; provenance DOIs are retained",
                       "No KRAS/MRTX1133 activity inference and no clinical recommendation"]}


def main():
    """Build the table, write the JSON and CSV files and a run receipt, and print a short summary."""
    # Start a timer for the run receipt.
    started = time.perf_counter()
    # Build the table, then write it in two formats.
    result = build_table()
    out = ROOT / "data/outputs"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "measured_activity_curation.json"
    path.write_bytes(json_bytes(result))
    csv_path = out / "measured_activity_curation.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["rows"][0]))
        writer.writeheader(); writer.writerows(result["rows"])
    # The run receipt: time, versions, zero network calls, and the hashes of the code and outputs. The saved 'command' text is the one used when the receipt was produced; in this repository run  python code/curate_activities.py.
    receipt = {"generated_utc": datetime.now(timezone.utc).isoformat(), "command": "Tools/ssd-run.sh python Playlists/ai-in-drug-discovery/4/code/curate_activities.py",
               "python": platform.python_version(), "platform": platform.platform(), "network_calls": 0,
               "elapsed_seconds": time.perf_counter() - started, "source_receipts_sha256": sha(ROOT / "research/download_receipts.json"),
               "code_sha256": sha(Path(__file__)), "outputs": {p.name: sha(p) for p in [path, csv_path]}}
    (out / "curation_run_receipt.json").write_bytes(json_bytes(receipt))
    # Print a short summary: counts and the single retained record.
    print(json.dumps({"source_rows": result["acquired_source_row_count"], "selected_rows": len(result["rows"]),
                      "counts": result["counts"], "retained": [{k:r[k] for k in ["activity_id", "assay_chembl_id", "standard_value", "standard_units", "curation_status"]} for r in result["rows"] if r["curation_status"].startswith("retained")],
                      "pooled_assays": 0}, indent=2))


if __name__ == "__main__":
    main()
