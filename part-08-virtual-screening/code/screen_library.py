"""Reload the exact Part 7 ensemble and use it to make two comparable EGFR candidate shortlists from a frozen library.

What this file does
    1. Reads the frozen library of 456 structures (ChEMBL catalogue entries and structure-only virtual analogues).
    2. Checks that the Part 7 model on disk is exactly the one verified at the end of Part 7 (SHA-256 fingerprint).
    3. Regenerates the same Part 5 features for every candidate and scores it with the saved model (predicted pIC50, interval, nearest training structure).
    4. Applies two gates: predicted pIC50 of at least 7.0 and a nearest-training-structure Tanimoto above the model's support cutoff.
    5. Clusters the candidates that passed both gates (Butina, distance 0.20), then picks 20 cluster centroids with MaxMin.
    6. Writes the 20-row CSV with provenance, a report and all candidate scores.

What it needs
    The libraries of Part 7 (NumPy, scikit-learn, XGBoost, joblib, RDKit, PyArrow), the Part 7 folder with the saved model,
    and the Part 5 handoff folder with feature_handoff.py.

Run
    python code/screen_library.py

What to expect
    One short JSON line: how many candidates were scored, how many passed both gates, the cluster count, 20 selected, and the CSV name.
"""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

from selection import butina_clusters, distance_matrix, maxmin, selection_summary

ROOT = Path(__file__).resolve().parent.parent
# The repository root holds every part folder; Part 8 reuses code and data from Part 5 and Part 7.
COURSE = ROOT.parent
CHAPTER_7 = COURSE / "part-07-qsar-python"
CHAPTER_5 = COURSE / "part-05-molecules-as-data-smiles-fingerprints-and-graphs/code"
# Make the Part 7 code and the Part 5 handoff importable.
for source in (CHAPTER_7 / "code", CHAPTER_5):
    if source.is_dir():
        sys.path.append(str(source))

from feature_handoff import feature_rows  # noqa: E402
from saved_model import open_model, predict_features  # noqa: E402

# The fingerprint of the exact Part 7 model file; the screen stops if the model on disk differs.
MODEL_SHA256 = "0fb37847a2303f9af14683b36b5098344b8bb8ab8840bc00b113b361e2db90d1"
# Gate 1: a candidate needs a predicted pIC50 of at least 7 (IC50 about 100 nM or lower).
POTENCY_FLOOR = 7.0
# Sphere radius for Butina clustering: molecules closer than 0.20 (Tanimoto distance) share a cluster.
BUTINA_DISTANCE = 0.20
# The shortlist length that was declared before looking at any scores.
SELECTION_BUDGET = 20


def file_hash(path: Path) -> str:
    """Return the SHA-256 fingerprint of a file."""
    return sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    """Write JSON through a temporary file, so a stopped run never leaves a half-written file."""
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def candidates_from_library(library: dict, manifest: dict) -> list[dict[str, Any]]:
    """Require release identity and one unseen structural identity per candidate."""
    # The library must declare its source release and the scope of its activity check.
    if library["release"] != "ChEMBL_37" or not library["scope"] or not library["candidates"]:
        raise ValueError("Use the declared ChEMBL 37 catalogue and activity-check scope")
    candidates = library["candidates"]
    keys = {row["inchikey"] for row in candidates}
    identifiers = {row["compound_id"] for row in candidates}
    # Every candidate must be a different structure with its own identifier.
    if len(keys) != len(candidates) or len(identifiers) != len(candidates):
        raise ValueError("Library repeats a structure or compound identifier")
    # No candidate may be one of the molecules the model was trained or tested on.
    if not keys.isdisjoint(manifest["all_measured_cohort_identities"]):
        raise ValueError("The prospective pool includes a measured Video 7 compound")
    # A prospective candidate has no measured potency for this assay.
    for row in candidates:
        if row.get("measured_pic50") is not None or row.get("pic50") is not None:
            raise ValueError("Verified unknown EGFR potency is expected in this prospective collection")
    return candidates


def score_library(candidates: list[dict], artifact: dict) -> list[dict]:
    """Regenerate the same Chapter 5 features before scoring in bounded batches."""
    # Recompute the Part 5 feature rows and sort them by compound ID, so the order is always the same.
    features = sorted(feature_rows(candidates), key=lambda row: row["compound_id"])
    provenance = {row["compound_id"]: row.get("structure_source", "chembl_catalogue") for row in candidates}
    results = []
    # Score 256 molecules at a time to keep memory use small.
    for offset in range(0, len(features), 256):
        batch = features[offset:offset + 256]
        predictions = predict_features(artifact, batch)
        for features_row, score in zip(batch, predictions):
            results.append({**score, "smiles": features_row["canonical_isomeric_smiles"],
                            "morgan_on_bits": features_row["morgan_on_bits"], "measured_pic50": None,
                            "structure_source": provenance[score["compound_id"]],
                            "passes_potency": score["predicted_pic50"] >= POTENCY_FLOOR})
    return results


def shortlist(scores: list[dict], budget: int = SELECTION_BUDGET) -> tuple[dict, list[dict]]:
    """Apply both candidate gates, cluster the passing rows and select actual centers."""
    # Keep only the candidates that pass both gates: predicted potency and structural support.
    active = [row for row in scores if row["passes_potency"] and row["passes_applicability"]]
    # Table of 1 - Tanimoto distances between every pair of passing candidates.
    distances = distance_matrix([row["morgan_on_bits"] for row in active])
    # Sphere exclusion: each cluster has a real molecule as its centroid, listed first.
    groups = butina_clusters(distances, BUTINA_DISTANCE)
    group_rows = [{"cluster_id": group + 1, "centroid": active[members[0]]["compound_id"],
                   "members": [active[member]["compound_id"] for member in members]}
                  for group, members in enumerate(groups)]
    centers = [group[0] for group in groups]
    # MaxMin chooses among the centroids, so each pick represents a different region of structure space.
    chosen, trace = maxmin(active, distances, centers, budget)
    # The comparison list: the same number of candidates taken purely by the highest predicted pIC50.
    score_only = sorted(range(len(active)), key=lambda index: (-active[index]["predicted_pic50"],
                                                                 active[index]["compound_id"]))[:len(chosen)]
    cluster_ids = {row["centroid"]: row["cluster_id"] for row in group_rows}
    selected = [{**active[index], "maxmin_rank": rank, "cluster_id": cluster_ids[active[index]["compound_id"]],
                 "selection_min_distance": trace[rank - 1]["min_distance_to_selected"]}
                for rank, index in enumerate(chosen, 1)]
    summary = {
        "scored": len(scores), "passes_potency_only_or_both": sum(row["passes_potency"] for row in scores),
        "passes_support_only_or_both": sum(row["passes_applicability"] for row in scores),
        "passes_both": len(active), "pairs": len(active) * (len(active) - 1) // 2, "clusters": group_rows,
        "cluster_count": len(groups), "eligible_centroids": len(centers), "selected_count": len(chosen),
        "maxmin": selection_summary(active, distances, chosen),
        "score_only": selection_summary(active, distances, score_only), "trace": trace,
    }
    return summary, selected


def export_csv(path: Path, selected: list[dict], library_sha: str, manifest: dict) -> None:
    """Keep compound identities and model provenance together for downstream matching."""
    # Columns: the pick and its identity, the prediction with its interval, then provenance for later lessons.
    fields = ["maxmin_rank", "compound_id", "identity", "smiles", "structure_source", "predicted_pic50", "interval_lower_pic50",
              "interval_upper_pic50", "nearest_training_identity", "nearest_training_tanimoto", "cluster_id",
              "selection_min_distance", "measured_pic50", "source_release", "screen_target_assay", "model_sha256",
              "library_sha256", "cell_painting_status", "admet_status"]
    temporary = path.with_suffix(".pending")
    with temporary.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in selected:
            # The status columns say that later lessons still have to match Cell Painting profiles and evaluate ADMET.
            writer.writerow({**row, "source_release": "ChEMBL_37", "screen_target_assay": manifest["target_assay"],
                             "model_sha256": manifest["model_sha256"], "library_sha256": library_sha,
                             "cell_painting_status": "pending_match", "admet_status": "pending_evaluation"})
    temporary.replace(path)


def run(library_path: Path, manifest_path: Path, output: Path) -> dict:
    """Run the whole screen and write the CSV, the report and the candidate scores into the output folder."""
    library = json.loads(library_path.read_text())
    manifest_on_disk = json.loads(manifest_path.read_text())
    # Stop at once if the model is not exactly the verified Part 7 model.
    if manifest_on_disk["model_sha256"] != MODEL_SHA256:
        raise ValueError("Video 8 requires the exact model verified at the end of Video 7")
    manifest, artifact = open_model(manifest_path)
    candidates = candidates_from_library(library, manifest)
    scores = score_library(candidates, artifact)
    summary, selected = shortlist(scores)
    library_sha = file_hash(library_path)
    output.mkdir(parents=True, exist_ok=True)
    # A complete 20-row list gets the final name; fewer rows would be saved as a partial list.
    finished = len(selected) == SELECTION_BUDGET
    name = "egfr_20_diverse_hits.csv" if finished else "egfr_diverse_hits_partial.csv"
    shortlist_path = output / name
    export_csv(shortlist_path, selected, library_sha, manifest)
    report = {"model_sha256": manifest["model_sha256"], "model_manifest_sha256": file_hash(manifest_path),
              "library_sha256": library_sha, "release": library["release"], "library_check_scope": library["scope"],
              "potency_floor": POTENCY_FLOOR, "minimum_nearest_training_tanimoto": artifact["applicability_min_tanimoto"],
              "butina_distance_threshold": BUTINA_DISTANCE, "requested_budget": SELECTION_BUDGET,
              "met_budget": finished, "shortlist": name, "shortlist_sha256": file_hash(shortlist_path), **summary}
    write_json(output / "SCREEN_REPORT.json", report)
    write_json(output / "CANDIDATE_SCORES.json", {"candidates": scores, "model_sha256": manifest["model_sha256"],
                                                  "library_sha256": library_sha})
    return report


if __name__ == "__main__":
    # Command line options let you point the screen at other files; the defaults match this repository.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=ROOT / "data/source/COMBINED_LIBRARY.json")
    parser.add_argument("--manifest", type=Path, default=CHAPTER_7 / "data/trained/MODEL_MANIFEST.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/output")
    arguments = parser.parse_args()
    receipt = run(arguments.library, arguments.manifest, arguments.output)
    print(json.dumps({key: receipt[key] for key in ("scored", "passes_both", "cluster_count", "selected_count", "shortlist")}))
