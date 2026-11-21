"""Repeat the similarity, sphere-exclusion and MaxMin teaching calculations from the Part 8 lesson.

What this file does
    It builds the small tables shown in the video:
      * Tanimoto similarity and distance of the bit sets {1, 3, 5} and {1, 5, 7};
      * a five-molecule distance table, the neighbors within 0.34 and the Butina clusters (centroid first);
      * the MaxMin choice of three from five candidates, compared with simply taking the three highest scores.

What it needs
    Python 3.10 or newer, NumPy and RDKit. No downloaded data.

Run
    python code/worked_examples.py

What to expect
    A JSON printout. For example the Tanimoto similarity is 0.5 (2 shared bits of 4), the Butina clusters are
    [B, A, C] and [E, D], and MaxMin chooses A, C and E.
"""

import json

from selection import butina_clusters, distance_matrix, maxmin, selection_summary


def examples() -> dict:
    """Calculate every small example of the lesson and return the numbers as a dictionary."""
    # Tanimoto similarity = shared bits / all bits: {1, 3, 5} and {1, 5, 7} share 2 of 4 bits, so 0.5.
    one, two = {1, 3, 5}, {1, 5, 7}
    # Five tiny fingerprints (A to E) give a distance table; sphere radius 0.34.
    cluster_matrix = distance_matrix([[1, 2], [1, 2, 3], [1, 3], [8, 9], [8, 9, 10]])
    groups = butina_clusters(cluster_matrix, 0.34)
    # Five candidates with predicted pIC50 values, then a different table of distances for the MaxMin example.
    candidates = [{"compound_id": name, "predicted_pic50": score}
                  for name, score in zip("ABCDE", [8.0, 7.9, 7.7, 7.6, 7.4])]
    selection_matrix = distance_matrix([[1, 2], [1, 2, 3], [7, 8], [1, 7], [3, 4]])
    # MaxMin: start from the best score, then repeatedly add the candidate farthest from all chosen ones.
    chosen, trace = maxmin(candidates, selection_matrix, list(range(5)), 3)
    return {
        "tanimoto": {"left": sorted(one), "right": sorted(two), "intersection": sorted(one & two),
                     "union": sorted(one | two), "similarity": len(one & two) / len(one | two),
                     "distance": 1.0 - len(one & two) / len(one | two)},
        "butina": {"cutoff": 0.34, "distance_table": cluster_matrix.tolist(),
                   "neighbors": {"ABCDE"[i]: ["ABCDE"[j] for j, d in enumerate(row) if i != j and d <= 0.34]
                                 for i, row in enumerate(cluster_matrix)},
                   "clusters_centroid_first": [["ABCDE"[i] for i in group] for group in groups]},
        "maxmin": {"distance_table": selection_matrix.tolist(), "trace": trace,
                   "diverse": selection_summary(candidates, selection_matrix, chosen),
                   "score_only": selection_summary(candidates, selection_matrix, [0, 1, 2])},
    }


if __name__ == "__main__":
    print(json.dumps(examples(), indent=2, allow_nan=False))
