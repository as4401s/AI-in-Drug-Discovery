"""Prepare the model inputs: a number table X from the Part 5 structure columns, and a vector y of measurements.

What this file does
    * make_matrix turns each molecule's fingerprint positions and descriptors into one row of numbers.
    * match_labels attaches the measured pIC50 to each row, using the structure identity (the InChIKey) as the key.
    * nearest_support finds the closest known molecule to a query using the Tanimoto similarity from Part 5.

What it needs
    Python 3.10 or newer and NumPy. It does not need RDKit, because the fingerprints were already computed in Part 5.

What to expect
    A matrix with one row per molecule and 2,222 columns: 2,048 Morgan bits, 167 MACCS bits and 7 descriptors.
"""

from collections.abc import Mapping, Sequence
from math import isfinite
from numbers import Integral
from typing import Any

import numpy as np
from numpy.typing import NDArray

# The fingerprint sizes and the descriptor names are fixed, so every molecule is described in the same order.
MORGAN_BITS = 2048
MACCS_BITS = 167
DESCRIPTORS = ("MolWt", "MolLogP", "TPSA", "HBD", "HBA", "heavy_atoms", "rotatable_bonds")


def make_matrix(features: Sequence[Mapping[str, Any]]) -> NDArray[np.float64]:
    """Expand the on-bit positions and append descriptors in a fixed order.

    features: one dictionary per molecule, with 'morgan_on_bits', 'maccs_on_bits' and the descriptor values.
    Returns a NumPy array with one row per molecule: [Morgan bits | MACCS bits | descriptors].
    """
    # The descriptors start after both fingerprints, so this is the first descriptor column.
    first_descriptor = MORGAN_BITS + MACCS_BITS
    # Start from a table of zeros; a 1.0 will mark every fingerprint bit that is switched on.
    matrix = np.zeros((len(features), first_descriptor + len(DESCRIPTORS)), dtype=np.float64)
    for index, row in enumerate(features):
        # Handle the two fingerprints with the same steps; offset says where each one starts in the row.
        for column, width, offset, name in (
            ("morgan_on_bits", MORGAN_BITS, 0, "Morgan"),
            ("maccs_on_bits", MACCS_BITS, MORGAN_BITS, "MACCS"),
        ):
            bits = row[column]
            # Check that every position is a whole number inside the fingerprint, so a bad file is caught early.
            if any(isinstance(bit, bool) or not isinstance(bit, Integral) or not 0 <= bit < width for bit in bits):
                raise ValueError(f"{row['standard_inchi_key']}: invalid {name} fingerprint position")
            # Switch on the listed positions (shifted by the offset) in this molecule's row.
            matrix[index, np.asarray(bits, dtype=np.intp) + offset] = 1.0

        # Append the seven descriptors as ordinary numbers after the fingerprint bits.
        values = [float(row[name]) for name in DESCRIPTORS]
        if not all(isfinite(value) for value in values):
            raise ValueError(f"{row['standard_inchi_key']}: descriptors need to be finite numbers")
        matrix[index, first_descriptor:] = values
    return matrix


def match_labels(
    features: Sequence[Mapping[str, Any]], labels: Sequence[Mapping[str, Any]],
) -> NDArray[np.float64]:
    """Join the measured pIC50 by structure, preserving the feature table order.

    features: the structure rows (each has 'standard_inchi_key').
    labels: the measurement rows (each has 'inchikey' and 'pic50').
    Returns the vector y, in the same order as the feature rows.
    """
    # Look up each measured pIC50 by the structure's InChIKey.
    by_identity = {row["inchikey"]: float(row["pic50"]) for row in labels}
    feature_keys = [row["standard_inchi_key"] for row in features]
    # Each structure must appear exactly once in both tables; a duplicate would silently double count it.
    if len(by_identity) != len(labels) or len(set(feature_keys)) != len(feature_keys):
        raise ValueError("Activity and feature tables need unique identities; found a duplicate")
    # Both tables must describe the same molecules, with none missing and none extra.
    if set(feature_keys) != set(by_identity):
        raise ValueError("Activity and feature tables need the same structural identities")
    # Build y by walking the feature table, so row i of X and entry i of y belong to the same molecule.
    values = np.asarray([by_identity[key] for key in feature_keys], dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Observed pIC50 needs to be finite")
    return values


def nearest_support(query: Sequence[int], reference: Mapping[str, Sequence[int]]) -> tuple[str, float]:
    """Find the closest observed reference on the same ordered bit definition.

    query: the on-bit positions of the molecule we ask about.
    reference: a dictionary from identity to on-bit positions of each known molecule.
    Returns the identity of the most similar known molecule and its Tanimoto similarity (0 to 1).
    """
    query_bits = set(query)
    if not query_bits or not reference:
        raise ValueError("Similarity needs a nonempty fingerprint and reference set")

    closest_identity = ""
    highest_similarity = -1.0
    # Visit the references in sorted order so a tie always gives the same answer.
    for identity, fingerprint in sorted(reference.items()):
        known_bits = set(fingerprint)
        # Tanimoto similarity = bits both molecules share / bits either molecule has.
        similarity = len(query_bits & known_bits) / len(query_bits | known_bits)
        if similarity > highest_similarity:
            closest_identity = identity
            highest_similarity = similarity
    return closest_identity, highest_similarity
