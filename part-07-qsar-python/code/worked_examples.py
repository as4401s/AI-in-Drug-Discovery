"""Repeat the small hand calculations from the Part 7 lesson, before any model sees the real assay data.

What this file does
    It computes, with a few numbers each, the same examples the video draws on the boards:
    pIC50 from IC50, a decision tree's leaf averages, a forest's average, one boosting round,
    one neural-network update, one message-passing step on the chain C-C-O, a regression-metrics example,
    and the calibration rank that gives an interval half-width.

What it needs
    Python 3.10 or newer and NumPy. No RDKit and no downloaded data.

Run
    python code/worked_examples.py

What to expect
    A JSON printout. For example potency [7, 8], forest prediction 7, boosted predictions [6.5, 7.5],
    next MLP weight 1.2 and the interval [6.2, 7.8].
"""

from math import ceil
import json

import numpy as np

from evaluation import regression_metrics


def examples():
    """Calculate the small examples before any models see the real assay data."""
    # pIC50 = 9 - log10(IC50 in nM): 100 nM gives 7, 10 nM gives 8.
    potency = 9 - np.log10([100, 10])
    leaf_values = np.array([6.0, 7.0, 8.0])
    split_values = np.array([[6.0, 7.0], [8.0, 9.0]])

    # With squared loss, the residual is the amount each current prediction missed.
    # Boosting starts from the mean, then adds half of the residual as a correction.
    observed = np.array([6.0, 8.0])
    first = np.full_like(observed, observed.mean())
    residual = observed - first
    boosted = first + 0.5 * residual

    # The toy chain C-C-O uses features 1, 1 and 2 to make each averaging step visible.
    # Each atom hears the mean of its neighbors: the two end atoms have one neighbor, the middle atom has two.
    node = np.array([1.0, 1.0, 2.0])
    neighboring = np.array([node[1], (node[0] + node[2]) / 2, node[1]])
    hidden = np.maximum(0.5 * node + neighboring, 0)
    graph_prediction = 4 + 1.2 * hidden.mean()

    # Each error here is the worst absolute error within a toy calibration scaffold.
    # Take the ceil((n + 1) x 0.8)-th smallest of the four group scores as the half-width.
    ordered = sorted([0.25, 0.8, 0.15, 0.4])
    rank = ceil((len(ordered) + 1) * 0.8)
    width = ordered[rank-1]

    # One neural-network update: prediction = input x weight x weight = 1 x 1 x 1, target 2.
    # The gradient of the squared error is 2 x (prediction - target); the new weight moves against it.
    prediction = 1.0 * 1.0 * 1.0
    target = 2.0
    gradient = 2 * (prediction - target)
    next_weight = 1.0 - 0.1 * gradient
    return {
        "potency": potency.tolist(),
        "tree": {"observed_by_leaf": split_values.tolist(), "leaf_predictions": split_values.mean(axis=1).tolist()},
        "forest": {"tree_predictions": leaf_values.tolist(), "prediction": float(leaf_values.mean())},
        "boosting": {
            "initial_predictions": first.tolist(),
            "initial_residuals": residual.tolist(),
            "predictions": boosted.tolist(),
            "mse_before": float(np.mean((first-observed)**2)),
            "mse_after": float(np.mean((boosted-observed)**2)),
        },
        "mlp": {"prediction": prediction, "gradient": gradient, "next_weight": next_weight,
                "next_loss": round((next_weight-target)**2, 12)},
        "graph": {"atoms": node.tolist(), "neighbor_means": neighboring.tolist(), "hidden": hidden.tolist(),
                  "pooled": float(hidden.mean()), "prediction": graph_prediction},
        "evaluation": {"observed": [6, 7, 8], "predicted": [6, 8, 7],
                       **regression_metrics([6, 7, 8], [6, 8, 7])},
        "calibration": {"ordered_scaffold_errors": ordered, "ordered_rank": rank, "half_width": width,
                        "interval": [round(7-width, 12), round(7+width, 12)]},
    }


if __name__ == "__main__":
    print(json.dumps(examples(), indent=2))
