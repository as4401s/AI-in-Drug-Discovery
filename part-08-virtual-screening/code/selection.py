"""Compare molecular fingerprints, cluster them with Butina sphere exclusion and choose a diverse subset with MaxMin.

What this file does
    * distance_matrix turns each molecule's Morgan bits into a fingerprint and fills a table of 1 - Tanimoto distances.
    * butina_clusters draws a sphere of a given distance around real molecules and groups the molecules inside it.
    * maxmin picks molecules one at a time, each time taking the candidate whose nearest already-chosen molecule is farthest away.
    * selection_summary reports the same diversity numbers for any shortlist, so two shortlists of equal size can be compared.

What it needs
    Python 3.10 or newer, NumPy and RDKit.

What to expect
    Small inputs give small tables you can check by hand (see worked_examples.py). The screen in screen_library.py uses the same functions on 456 molecules.
"""

from collections.abc import Sequence
from itertools import combinations
from typing import Any

import numpy as np
from rdkit import DataStructs
from rdkit.ML.Cluster import Butina


def distance_matrix(bit_positions: Sequence[Sequence[int]], bit_count: int = 2048) -> np.ndarray:
    """Calculate 1 − Tanimoto once per pair and store it on both sides of the diagonal.

    bit_positions: for each molecule, the positions of its on-bits. Returns a square table of distances
    (0 = identical fingerprints, 1 = no shared bits).
    """
    vectors = []
    for bits in bit_positions:
        # A fingerprint needs at least one on-bit, and every position has to lie inside the 2,048-bit space.
        if not bits or any(not 0 <= bit < bit_count for bit in bits):
            raise ValueError("Expected a nonempty fingerprint in the declared bit space")
        # RDKit stores a fingerprint as a row of bits; switch on the listed positions.
        vector = DataStructs.ExplicitBitVect(bit_count)
        vector.SetBitsFromList(list(bits))
        vectors.append(vector)
    distances = np.zeros((len(vectors), len(vectors)))
    # Fill the table row by row: compare each molecule with all molecules before it and mirror the result.
    for index, vector in enumerate(vectors[1:], 1):
        row = DataStructs.BulkTanimotoSimilarity(vector, vectors[:index], returnDistance=True)
        distances[index, :index] = distances[:index, index] = row
    return distances


def butina_clusters(distances: np.ndarray, cutoff: float) -> tuple[tuple[int, ...], ...]:
    """Treat close neighbors as a sphere around a real molecule, returned first.

    distances: the square distance table. cutoff: the sphere radius, as a distance.
    Returns clusters as tuples of row numbers; the first number of each tuple is the centroid, a real molecule.
    """
    if not 0 < cutoff <= 1 or distances.ndim != 2 or distances.shape[0] != distances.shape[1]:
        raise ValueError("Use a square distance matrix and a cutoff in (0, 1]")
    if not len(distances):
        return ()
    # Reordering recalculates the neighbor count after each assigned sphere is removed.
    return Butina.ClusterData(distances, len(distances), cutoff, isDistData=True, reordering=True)


def maxmin(
    rows: list[dict[str, Any]], distances: np.ndarray, representatives: Sequence[int], budget: int,
) -> tuple[list[int], list[dict[str, Any]]]:
    """Seed on potency and repeatedly maximize the nearest distance to the shortlist.

    rows: candidate dictionaries with 'compound_id' and 'predicted_pic50'. representatives: the row numbers allowed
    to be chosen (the cluster centroids). budget: how many to choose.
    Returns the chosen row numbers and a trace that records every option at every step.
    """
    if budget < 1 or len(set(representatives)) != len(representatives):
        raise ValueError("The budget needs to be positive and representatives must be unique")
    remaining = set(representatives)
    if not remaining:
        return [], []

    def score_order(index: int) -> tuple[float, str]:
        """Sort key: highest predicted pIC50 first, and the compound ID breaks exact ties."""
        return -rows[index]["predicted_pic50"], rows[index]["compound_id"]

    # Step 1: start from the candidate with the highest predicted potency.
    first = min(remaining, key=score_order)
    chosen = [first]
    remaining.remove(first)
    trace = [{"step": 1, "choice": rows[first]["compound_id"], "min_distance_to_selected": None,
              "basis": "Highest predicted pIC50 among cluster centroids"}]
    # Next steps: for every remaining candidate, find its distance to the nearest chosen molecule, then take the largest.
    while remaining and len(chosen) < budget:
        distance_and_neighbor = {
            index: min((float(distances[index, selected]), rows[selected]["compound_id"]) for selected in chosen)
            for index in remaining
        }
        # Rank by that nearest distance (largest first); potency and ID only break ties.
        ranked = sorted(remaining, key=lambda index: (-distance_and_neighbor[index][0], *score_order(index)))
        winner = ranked[0]
        # Record all options and their distances so the video can show the decision at every step.
        trace.append({"step": len(chosen) + 1, "choice": rows[winner]["compound_id"],
                      "min_distance_to_selected": distance_and_neighbor[winner][0],
                      "selected_before": [rows[index]["compound_id"] for index in chosen],
                      "options": [{"id": rows[index]["compound_id"], "predicted_pic50": rows[index]["predicted_pic50"],
                                   "min_distance_to_selected": distance_and_neighbor[index][0],
                                   "closest_selected": distance_and_neighbor[index][1],
                                   "distances": [float(distances[index, selected]) for selected in chosen]}
                                  for index in ranked]})
        chosen.append(winner)
        remaining.remove(winner)
    return chosen, trace


def selection_summary(rows: list[dict[str, Any]], distances: np.ndarray, chosen: Sequence[int]) -> dict[str, Any]:
    """Use the same mean and minimum pair distances for any equal-size shortlist.

    chosen: the row numbers of a shortlist. Returns the mean and the smallest pair distance inside it
    and the mean predicted pIC50.
    """
    # Every pair of chosen molecules gives one distance; a diverse list has large distances.
    pair_distances = [float(distances[a, b]) for a, b in combinations(chosen, 2)]
    return {
        "compound_ids": [rows[index]["compound_id"] for index in chosen],
        "mean_pairwise_distance": float(np.mean(pair_distances)) if pair_distances else None,
        "smallest_pairwise_distance": min(pair_distances) if pair_distances else None,
        "mean_predicted_pic50": float(np.mean([rows[index]["predicted_pic50"] for index in chosen])) if chosen else None,
    }
