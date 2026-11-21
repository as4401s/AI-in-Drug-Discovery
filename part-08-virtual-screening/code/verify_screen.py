"""Audit the Part 8 screen: the library, the shortlist, every MaxMin step and an offline replay.

What this file does
    It re-checks the saved outputs against the inputs, step by step, using plain Python set and distance arithmetic
    that is independent of the screening code:
      * the model file and the library match their recorded SHA-256 fingerprints;
      * every candidate is a different structure and none was measured in Part 7;
      * the eligible set is exactly the candidates that pass both gates, and each cluster fits inside the Butina radius;
      * every MaxMin choice is re-derived from the distances;
      * the 20-row CSV matches the choices and carries the provenance columns;
      * a fresh run of the screen reproduces the saved files byte for byte.

What it needs
    The same libraries as screen_library.py and the files already written to data/output/.

Run
    python code/verify_screen.py

What to expect
    A JSON receipt. An AssertionError names the first check that failed.
"""

import csv
import json
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory

from screen_library import CHAPTER_7, MODEL_SHA256, ROOT, file_hash, run


def json_file(file: Path) -> dict:
    """Read a JSON file into a dictionary."""
    return json.loads(file.read_text())


def bit_distance(left: dict, right: dict) -> float:
    """Tanimoto distance of two candidates, computed directly from their on-bit sets."""
    a, b = set(left["morgan_on_bits"]), set(right["morgan_on_bits"])
    return 1.0 - len(a & b) / len(a | b)


def verify(root: Path) -> dict:
    """Run every audit check on the Part 8 folder and return the evidence as a dictionary."""
    library_path = root / "data/source/COMBINED_LIBRARY.json"
    source_lock = json_file(root / "data/source/COMBINED_LIBRARY_LOCK.json")
    library = json_file(library_path)
    output = root / "data/output"
    report = json_file(output / "SCREEN_REPORT.json")
    predictions = json_file(output / "CANDIDATE_SCORES.json")["candidates"]
    by_id = {row["compound_id"]: row for row in predictions}
    manifest = CHAPTER_7 / "data/trained/MODEL_MANIFEST.json"
    model_info = json_file(manifest)
    # The model and the library on disk are the ones named in the report and the lock.
    assert file_hash(manifest.parent / model_info["file"]) == report["model_sha256"] == MODEL_SHA256
    assert file_hash(library_path) == report["library_sha256"] == source_lock["library_sha256"]
    ids = {row["compound_id"] for row in library["candidates"]}
    exact_keys = {row["inchikey"] for row in library["candidates"]}
    # The first block of an InChIKey identifies the molecular connectivity, ignoring stereochemistry.
    connectivity = {key.partition("-")[0] for key in exact_keys}
    virtual = [row["inchikey"].partition("-")[0] for row in library["candidates"]
               if row["structure_source"] == "virtual_analogue"]
    catalogue = {row["inchikey"].partition("-")[0] for row in library["candidates"]
                 if row["structure_source"] == "chembl_catalogue"}
    remembered = {key.partition("-")[0] for key in model_info["all_measured_cohort_identities"]}
    # Catalogue entries can represent different stereochemistry at the same connectivity.
    # Every candidate is unique, was scored, and shares no structure with the Part 7 measured molecules.
    assert len(ids) == len(exact_keys) == len(library["candidates"]) and set(by_id) == ids
    assert len(virtual) == len(set(virtual)) and set(virtual).isdisjoint(catalogue)
    assert remembered.isdisjoint(connectivity)

    # The eligible set must be exactly the candidates that pass both gates.
    eligible = {key for key, row in by_id.items() if row["predicted_pic50"] >= report["potency_floor"]
                and row["nearest_training_tanimoto"] >= model_info["applicability_min_tanimoto"]}
    clusters = report["clusters"]
    member_ids = [member for group in clusters for member in group["members"]]
    # Every eligible candidate sits in exactly one cluster.
    assert set(member_ids) == eligible and len(member_ids) == len(eligible)
    for group in clusters:
        first, *neighbors = group["members"]
        # The centroid is listed first, and every member lies within the sphere around it.
        assert first == group["centroid"]
        assert all(bit_distance(by_id[first], by_id[other]) <= report["butina_distance_threshold"] + 1e-12
                   for other in neighbors)

    def score_order(identifier: str) -> tuple[float, str]:
        """Sort key: highest predicted pIC50 first, and the compound ID breaks exact ties."""
        return -by_id[identifier]["predicted_pic50"], identifier

    # Re-derive the MaxMin choices from scratch and compare them with the saved trace.
    remaining = {group["centroid"] for group in clusters}
    selected = []
    for step in report["trace"]:
        if not selected:
            winner = min(remaining, key=score_order)
        else:
            free_distance = {candidate: min(bit_distance(by_id[candidate], by_id[prior]) for prior in selected)
                             for candidate in remaining}
            winner = min(remaining, key=lambda key: (-free_distance[key], *score_order(key)))
            assert abs(free_distance[winner] - step["min_distance_to_selected"]) < 1e-12
        assert step["choice"] == winner
        selected.append(winner)
        remaining.remove(winner)
    assert len(selected) == report["requested_budget"] == 20 and selected == report["maxmin"]["compound_ids"]
    # The comparison list is the 20 highest predicted pIC50 values among the eligible candidates.
    score_only = sorted(eligible, key=score_order)[:20]
    assert report["score_only"]["compound_ids"] == score_only
    # Recompute the mean and smallest pair distances of both lists and compare them with the report.
    for name, candidates in (("maxmin", selected), ("score_only", score_only)):
        distances = [bit_distance(by_id[left], by_id[right]) for left, right in combinations(candidates, 2)]
        assert abs(sum(distances) / len(distances) - report[name]["mean_pairwise_distance"]) < 1e-12
        assert abs(min(distances) - report[name]["smallest_pairwise_distance"]) < 1e-12

    # The CSV must match the choices, in order, and carry the provenance and pending-status columns.
    result_file = output / report["shortlist"]
    assert file_hash(result_file) == report["shortlist_sha256"]
    with result_file.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["compound_id"] for row in rows] == selected
    assert [int(row["maxmin_rank"]) for row in rows] == list(range(1, 21))
    for row in rows:
        assert row["model_sha256"] == MODEL_SHA256 and row["library_sha256"] == source_lock["library_sha256"]
        assert row["measured_pic50"] == "" and row["cell_painting_status"] == "pending_match"
        assert row["admet_status"] == "pending_evaluation" and row["structure_source"] == "virtual_analogue"
    # Finally, run the whole screen again into a temporary folder and compare the files byte for byte.
    with TemporaryDirectory(prefix="egfr-screen-replay-") as directory:
        fresh = Path(directory)
        run(library_path, manifest, fresh)
        replay = {name: file_hash(fresh / name) == file_hash(output / name) for name in
                  (report["shortlist"], "SCREEN_REPORT.json", "CANDIDATE_SCORES.json")}
        assert all(replay.values())
    return {"model_sha256": MODEL_SHA256, "catalogue_scanned": source_lock["catalogue_count"],
            "virtual_proposals": source_lock["virtual_count"], "screened": len(library["candidates"]),
            "eligible": len(eligible), "clusters": len(clusters), "chosen": len(selected),
            "unique_exact_compound_keys": len(exact_keys), "unique_connectivity_blocks": len(connectivity),
            "predeclared_budget_met": True, "no_documented_course_identity_overlap": True,
            "complete_partition_by_cluster_centroid": True, "independently_verified_maxmin_steps": len(selected),
            "byte_identical_screen_replay": replay, "measured_potency_present_rows": 0}


if __name__ == "__main__":
    print(json.dumps(verify(ROOT), indent=2))
