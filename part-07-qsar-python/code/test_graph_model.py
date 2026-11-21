"""Check the graph neighborhood arithmetic, the gradients and a genuine parameter update.

What it needs
    Python 3.10 or newer, NumPy and RDKit.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""

import unittest

import numpy as np
from rdkit import Chem

from graph_model import GraphBatch, graph_arrays, loss_and_gradients, predict


class MolecularGraphTests(unittest.TestCase):
    def test_minimal_graph_forward_and_permutation(self):
        """The C-C-O example predicts 6.2, and renumbering the atoms leaves the prediction unchanged."""
        graph = np.array([[1.0], [1.0], [2.0]])
        neighbours = np.array([[1.0], [1.5], [1.0]])
        original = GraphBatch.from_graphs([(graph, neighbours)])
        reverse = np.array([2, 1, 0])
        permuted = GraphBatch.from_graphs([(graph[reverse], neighbours[reverse])])
        parameters = [np.array([[0.5]]), np.array([[1.0]]), np.array([0.0]),
                      np.array([1.2]), np.array([4.0])]
        self.assertAlmostEqual(predict(original, parameters)[0], 6.2)
        np.testing.assert_allclose(predict(original, parameters), predict(permuted, parameters))

    def test_neighbor_weight_gradient(self):
        """Each analytic gradient matches a finite-difference slope, and a small downhill step lowers the loss."""
        batch = GraphBatch.from_graphs([
            (np.array([[1.0], [3.0]]), np.array([[3.0], [1.0]])),
            (np.array([[2.0]]), np.array([[0.0]])),
        ])
        parameters = [np.array([[0.5]]), np.array([[1.0]]), np.array([0.0]),
                      np.array([1.2]), np.array([0.5])]
        labels = np.array([2.0, 3.0])
        loss, grad = loss_and_gradients(batch, labels, parameters)
        epsilon = 0.00001
        for i, value in enumerate(parameters):
            before = value.flat[0]
            value.flat[0] = before + epsilon
            high, _ = loss_and_gradients(batch, labels, parameters)
            value.flat[0] = before - epsilon
            low, _ = loss_and_gradients(batch, labels, parameters)
            value.flat[0] = before
            self.assertAlmostEqual((high-low)/(2*epsilon), grad[i].flat[0], places=6)
        next_params = [a - 0.001*g for a, g in zip(parameters, grad)]
        self.assertLess(loss_and_gradients(batch, labels, next_params)[0], loss)

    def test_encoder_uses_real_edges(self):
        """The neighbor mean of each atom of ethanol comes from its real bonds."""
        node, neighbor = graph_arrays(Chem.MolFromSmiles("CCO"))
        self.assertEqual(len(node), 3)
        np.testing.assert_allclose(neighbor[1], (node[0] + node[2]) / 2)
        np.testing.assert_allclose(neighbor[0], node[1])
