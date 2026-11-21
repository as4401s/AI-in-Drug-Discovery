"""A small molecular graph neural network written in NumPy, so every step of message passing can be read.

What this file does
    * graph_arrays describes each atom with a short row of numbers and averages the rows of its bonded neighbors.
    * GraphBatch stacks the atoms of many molecules and remembers which molecule owns each row.
    * forward mixes each atom with its neighbors, pools the atoms of one molecule into one vector and predicts a value.
    * loss_and_gradients runs the backward pass, which gives the slope of the loss for every parameter.
    * fit_graph repeats "predict, measure the loss, move the parameters downhill" for a fixed number of steps.

What it needs
    Python 3.10 or newer and NumPy. RDKit supplies the molecule objects that graph_arrays reads.

What to expect
    A model with one message-passing layer. It is a teaching baseline: the lesson compares it with the tabular models.
"""

from dataclasses import dataclass

import numpy as np

# Atomic numbers that get their own column: C, N, O, F, P, S, Cl, Br, I. Any other element shares one "other" column.
ELEMENTS = (6, 7, 8, 9, 15, 16, 17, 35, 53)


def graph_arrays(molecule):
    """Encode atoms and calculate the mean feature vector across each bond neighborhood.

    molecule: an RDKit molecule. Returns (nodes, neighbors): one row per atom for the atom itself and for
    the average of its bonded neighbors.
    """
    atom_rows = []
    for atom in molecule.GetAtoms():
        number = atom.GetAtomicNum()
        # One row per atom: element one-hot, an "other element" flag, then degree, hydrogens, charge and aromaticity.
        atom_rows.append([
            *[int(number == element) for element in ELEMENTS],
            int(number not in ELEMENTS),
            atom.GetDegree() / 4,
            atom.GetTotalNumHs() / 4,
            atom.GetFormalCharge(),
            int(atom.GetIsAromatic()),
        ])
    nodes = np.array(atom_rows, dtype=float)
    counts = np.zeros(len(nodes))
    neighbor_sum = np.zeros_like(nodes)
    # Each bond passes a copy of each atom's row to the atom on the other end: that is the message.
    for bond in molecule.GetBonds():
        a, b = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        neighbor_sum[a] += nodes[b]
        neighbor_sum[b] += nodes[a]
        counts[[a, b]] += 1
    # Divide the summed messages by the number of neighbors to get the mean (an atom with no bond divides by 1).
    neighbors = neighbor_sum / np.maximum(1.0, counts[:, None])
    return nodes, neighbors


@dataclass(frozen=True)
class GraphBatch:
    """Keep the atom rows stacked and remember which molecule owns each row."""

    nodes: np.ndarray
    neighbors: np.ndarray
    graph_index: np.ndarray
    atom_counts: np.ndarray

    @classmethod
    def from_graphs(cls, graphs):
        """Group the nodes and neighbor means by molecule for vectorized training."""
        if not graphs:
            raise ValueError("A batch needs one or more molecules")
        nodes, neighbors = zip(*graphs)
        counts = np.array([len(matrix) for matrix in nodes])
        if np.any(counts == 0):
            raise ValueError("A molecule needs at least one atom")
        # Stack all atoms into one tall table; graph_index says which molecule each atom row belongs to.
        return cls(np.vstack(nodes), np.vstack(neighbors), np.repeat(np.arange(len(counts)), counts), counts)


def forward(batch, parameters):
    """Mix a node and its neighbors, then mean-pool the learned node activations.

    Returns the prediction for each molecule plus two intermediate arrays that the backward pass needs.
    """
    self_weights, neighbor_weights, bias, output_weights, output_bias = parameters
    # Each atom's new value = its own row x weights + its neighbors' mean row x weights + bias.
    activation_in = batch.nodes @ self_weights + batch.neighbors @ neighbor_weights + bias
    pooled = np.zeros((len(batch.atom_counts), len(bias)))
    # ReLU keeps positive values and sets negative ones to 0; then the atoms of each molecule are added together...
    np.add.at(pooled, batch.graph_index, np.maximum(activation_in, 0))
    # ...and divided by the atom count, which is mean pooling: one vector per molecule.
    pooled /= batch.atom_counts[:, None]
    # A final weighted sum turns the pooled vector into one predicted value.
    return pooled @ output_weights + output_bias, activation_in, pooled


def predict(batch, parameters):
    """Return one potency-scale value per molecular graph."""
    return forward(batch, parameters)[0]


def loss_and_gradients(batch, targets, parameters):
    """Differentiate mean squared error through the output, pooling and message weights.

    Returns the loss (mean squared error) and, for each parameter array, the slope of the loss (the gradient).
    """
    predicted, activation_in, pooled = forward(batch, parameters)
    # Error = prediction - measurement; the loss is the mean of the squared errors.
    error = predicted - targets
    # Backward pass: apply the chain rule from the output back to every parameter, one layer at a time.
    output_gradient = 2.0 * error / len(error)
    pooled_gradient = output_gradient[:, None] * parameters[3]
    node_gradient = pooled_gradient[batch.graph_index] / batch.atom_counts[batch.graph_index, None]
    # ReLU passes the slope only where its input was positive.
    activation_gradient = node_gradient * (activation_in > 0)
    return float(np.mean(error**2)), [
        batch.nodes.T @ activation_gradient,
        batch.neighbors.T @ activation_gradient,
        activation_gradient.sum(axis=0),
        pooled.T @ output_gradient,
        np.array([output_gradient.sum()]),
    ]


def fit_graph(batch, targets, *, width=16, steps=120, seed=7, learning_rate=0.025):
    """Fit a single message-passing layer and a graph-level regression output.

    width: how many hidden values each atom gets. steps: how many gradient-descent updates to run.
    learning_rate: how far to move the parameters along the downhill direction at each step.
    Returns the fitted parameters and the list of losses (the trace).
    """
    # A fixed seed gives the same starting parameters, so a run can be repeated exactly.
    generator = np.random.default_rng(seed)
    inputs = batch.nodes.shape[1]
    weights = [
        generator.normal(0, 0.2, size=(inputs, width)),
        generator.normal(0, 0.2, size=(inputs, width)),
        np.zeros(width),
        generator.normal(0, 0.15, size=width),
        # Start the output bias at the mean of the training targets, a sensible first guess.
        np.array([float(np.mean(targets))]),
    ]
    trace = []
    # The learning loop: predict, measure the loss, compute the gradients, step each parameter downhill.
    for _ in range(steps):
        loss, gradients = loss_and_gradients(batch, targets, weights)
        trace.append(loss)
        weights = [w - learning_rate * g for w, g in zip(weights, gradients)]
    # Record the loss after the final update too.
    trace.append(loss_and_gradients(batch, targets, weights)[0])
    return weights, trace
