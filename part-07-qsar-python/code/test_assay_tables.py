"""Check the Bemis-Murcko scaffold key on small reference structures.

What it needs
    Python 3.10 or newer and RDKit.

Run
    python -m unittest discover -s code -p 'test_*.py' -v

What to expect
    Every test passes (OK).
"""

import unittest

from assay_tables import scaffold_key


class ScaffoldTests(unittest.TestCase):
    def test_ring_analogs_keep_one_framework(self):
        """Molecules that differ only in side groups share one scaffold."""
        self.assertEqual(scaffold_key("c1ccccc1"), "c1ccccc1")
        self.assertEqual(scaffold_key("Cc1ccccc1"), "c1ccccc1")
        self.assertEqual(scaffold_key("CC1CCCCC1"), "C1CCCCC1")
        self.assertEqual(scaffold_key("c1ccccc1CCc2ccccc2"), "c1ccc(CCc2ccccc2)cc1")

    def test_acyclic_and_invalid_inputs_have_explicit_handling(self):
        """A molecule without rings joins the shared [acyclic] group; an invalid string raises an error."""
        self.assertEqual(scaffold_key("CC"), "[acyclic]")
        self.assertEqual(scaffold_key("CCO"), "[acyclic]")
        with self.assertRaises(ValueError):
            scaffold_key("invalid structure")
