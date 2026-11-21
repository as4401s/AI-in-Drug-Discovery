"""Hold out data fairly, score predictions, and put a calibrated range around them.

What this file does
    * split_membership assigns whole groups of molecules to development, calibration and test sets, without looking at any measurement.
    * calibration_width turns the largest error of each calibration group into one interval half-width (split conformal calibration).
    * regression_metrics reports MAE, RMSE, R squared and Spearman correlation for predicted against measured values.

What it needs
    Python 3.10 or newer and NumPy.

What to expect
    The functions return plain dictionaries and arrays, so every number can be printed and checked by hand.
"""

from collections import defaultdict
from collections.abc import Sequence
from itertools import groupby
from math import ceil, isfinite
from random import Random

import numpy as np
from numpy.typing import NDArray


def split_membership(identities, scaffolds, scheme, *, seed):
    """Return row indices with development, calibration and test membership kept separate.

    identities: one unique structure name per row (the InChIKey).
    scaffolds: the Bemis-Murcko scaffold of each row.
    scheme: 'random' keeps each molecule together; 'scaffold' keeps each whole scaffold group together.
    seed: fixed so the same split is produced on every run.
    """
    # Each molecule must appear once, otherwise the same structure could land in two sets.
    if len(identities) != len(scaffolds) or len(set(identities)) != len(identities):
        raise ValueError("The split needs one row per unique molecular identity")
    # The group key decides what stays together: a single molecule (random) or a whole scaffold (scaffold).
    if scheme == "random":
        keys = identities
    elif scheme == "scaffold":
        keys = scaffolds
    else:
        raise ValueError("Choose random or scaffold")
    if any(not key for key in keys):
        raise ValueError("Missing split group; assign acyclic structures explicitly")

    # Collect the row numbers that belong to each group.
    groups = defaultdict(list)
    for index, key in enumerate(keys):
        groups[key].append(index)
    ordered = sorted(groups)
    n_groups = len(ordered)
    # About 20% of the groups go to calibration and 20% to the test set, with a small minimum for each.
    n_cal = max(4, round(n_groups * 0.2))
    n_test = max(2, round(n_groups * 0.2))
    if n_groups - n_cal - n_test < 3:
        raise ValueError("Need three development groups, four calibration groups and two test groups")

    generator = Random(seed)
    expected = len(identities) * 0.2
    best = None
    # In the scaffold split one core may have far more compounds than another.
    # Search fixed, seeded membership proposals using only group sizes.
    proposals = 256 if scheme == "scaffold" else 1
    for _ in range(proposals):
        shuffled = generator.sample(ordered, n_groups)
        cal = shuffled[:n_cal]
        test = shuffled[n_cal:n_cal+n_test]
        development = shuffled[n_cal+n_test:]
        # Prefer the proposal whose calibration and test sets are closest to 20% of the molecules each.
        balance = abs(sum(len(groups[key]) for key in cal) - expected)
        balance += abs(sum(len(groups[key]) for key in test) - expected)
        if best is None or balance < best[0]:
            best = balance, development, cal, test

    # Convert the chosen groups back into sorted row numbers for each role.
    return {
        role: sorted(index for key in assigned for index in groups[key])
        for role, assigned in zip(("development", "calibration", "test"), best[1:])
    }


def calibration_width(absolute_errors, group_keys, *, coverage):
    """Take the finite-sample rank over maximum errors from calibration groups.

    absolute_errors: |measured - predicted| for each calibration molecule.
    group_keys: the group (scaffold or molecule) of each error.
    coverage: the share of new groups the range should contain, for example 0.8.
    Returns the ordered group scores, the rank used and the half-width of the interval.
    """
    if len(absolute_errors) != len(group_keys) or not 0 < coverage < 1:
        raise ValueError("Provide aligned errors and groups and a coverage between zero and one")
    # Keep only the largest error of each group, so a group counts once however many molecules it has.
    maximum = {}
    for error, key in zip(absolute_errors, group_keys):
        if not isfinite(error) or error < 0:
            raise ValueError("Calibration errors must be finite and nonnegative")
        maximum[key] = max(error, maximum.get(key, 0.0))
    ordered = sorted(maximum.values())
    # The finite-sample rule: take the ceil((n + 1) x coverage)-th smallest score.
    rank = ceil((len(ordered)+1) * coverage)
    if rank > len(ordered):
        raise ValueError("Too few calibration groups for a finite width at this coverage")
    return {"nominal_coverage": coverage, "group_count": len(ordered), "rank": rank,
            "ordered_scores": ordered, "half_width": float(ordered[rank-1])}


def _ranks(values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Assign the mean position to equal numbers, as in Spearman correlation."""
    ranks = np.empty(len(values), dtype=np.float64)
    next_rank = 1
    # Walk through the values from smallest to largest; equal values share the average of their positions.
    for _, indices in groupby(np.argsort(values), key=values.__getitem__):
        tied_indices = list(indices)
        last_rank = next_rank + len(tied_indices) - 1
        ranks[tied_indices] = (next_rank + last_rank) / 2.0
        next_rank = last_rank + 1
    return ranks


def regression_metrics(
    observed: Sequence[float] | NDArray[np.float64],
    predicted: Sequence[float] | NDArray[np.float64],
) -> dict[str, float | None]:
    """Describe scale errors, improvement over the mean and ordering agreement.

    observed: the measured pIC50 values. predicted: the model's values for the same molecules, in the same order.
    Returns MAE, RMSE, R squared and Spearman; a score that has no meaning (for example a flat column) is None.
    """
    actual = np.asarray(observed, dtype=np.float64)
    estimates = np.asarray(predicted, dtype=np.float64)
    if actual.ndim != 1 or actual.shape != estimates.shape or not actual.size:
        raise ValueError("Use one estimate per observed value")
    if not np.isfinite(actual).all() or not np.isfinite(estimates).all():
        raise ValueError("Measurements and estimates must be finite")

    # The error (residual) is prediction minus measurement, so a positive error means the model guessed too high.
    errors = estimates - actual
    squared_errors = np.square(errors)
    # Total variation: how far the measurements sit from their own mean. R squared compares the model to that mean.
    total_variation = np.square(actual - actual.mean()).sum()
    correlation = None
    # Spearman correlation needs both columns to vary; it is the ordinary correlation of the ranks.
    if np.ptp(actual) > 0 and np.ptp(estimates) > 0:
        correlation = float(np.corrcoef(_ranks(actual), _ranks(estimates))[0, 1])

    return {
        # MAE: the typical size of a miss, in pIC50 units.
        "mae": float(np.abs(errors).mean()),
        # RMSE: like MAE but larger misses count more, because errors are squared first.
        "rmse": float(np.sqrt(squared_errors.mean())),
        # R squared = 1 - (model squared error / squared error of always predicting the mean).
        "r2": float(1 - squared_errors.sum() / total_variation) if total_variation > 0 else None,
        "spearman": correlation,
    }
