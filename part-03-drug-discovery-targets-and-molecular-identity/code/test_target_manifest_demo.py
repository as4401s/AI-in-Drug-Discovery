"""Offline checks for mistakes that could silently join incompatible scientific records (Part 3)

Each test proves one safeguard of target_manifest_demo.py: a wrong mutation is refused, a compound is matched by
its full InChIKey, incompatible assay records are not joined, a tampered file is caught, and the real
structures keep construct changes and coordinates separate. No network is needed.

HOW TO RUN IT
  python -m unittest discover -s code -p "test_target_manifest_demo.py" -v
"""

# unittest runs the checks; importlib loads the script as a module; tempfile makes a throw-away folder for the tampering test.
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


# ROOT is the part folder; MODULE is the script under test, next to this file.
ROOT = Path(__file__).resolve().parents[1]
MODULE = Path(__file__).with_name("target_manifest_demo.py")


class TargetManifestTests(unittest.TestCase):
    """Safeguard checks for the Part 3 manifest builder."""
    def setUp(self):
        """Load target_manifest_demo.py as a module before every test (from the same code/ folder)."""
        self.assertTrue(MODULE.exists(), "the offline target-manifest implementation is missing")
        spec = importlib.util.spec_from_file_location("target_manifest_demo", MODULE)
        self.demo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.demo)

    def test_mutation_checks_reference_and_one_based_bounds(self):
        """A valid substitution works; position 0, a position past the end, a wrong original residue, a non-amino-acid letter and a 'change' to the same letter are all refused."""
        self.assertEqual(self.demo.apply_mutation("MAG", 2, "A", "D"), "MDG")
        for position, original, replacement in [(0, "M", "D"), (4, "G", "D"), (2, "G", "D"), (2, "A", "?"), (2, "A", "A")]:
            with self.subTest(position=position, original=original, replacement=replacement):
                with self.assertRaises(ValueError):
                    self.demo.apply_mutation("MAG", position, original, replacement)

    def test_compound_selection_uses_complete_inchikey_instead_of_first_name(self):
        """The exact MRTX1133 ligand is CHEMBL5081048, not the name-matched CHEMBL4858364; no match or a duplicated match raises an error."""
        candidates = json.loads((ROOT / "data/raw/chembl-mrtx1133-search.json").read_text())["molecules"]
        selected = self.demo.exact_compound(candidates, "SCLLZBIBSFTLIN-INOGPEIASA-N")
        self.assertEqual(selected["molecule_chembl_id"], "CHEMBL5081048")
        self.assertNotEqual(selected["molecule_chembl_id"], "CHEMBL4858364")
        with self.assertRaises(ValueError):
            self.demo.exact_compound(candidates, "NOT-A-MATCH")
        with self.assertRaises(ValueError):
            self.demo.exact_compound([selected, selected], "SCLLZBIBSFTLIN-INOGPEIASA-N")

    def test_join_requires_matching_variant_and_measurement_context(self):
        """Records join only if variant, endpoint, target and units all match; one different or missing key blocks the join."""
        a = {"target": "P01116-2", "variant": "G12D", "endpoint": "biochemical inhibition", "units": "nM"}
        keys = tuple(a)
        self.assertTrue(self.demo.assess_join(a, a, keys)["compatible"])
        for key, value in [("variant", "reference G12"), ("endpoint", "cell viability"), ("target", "P01116-1"), ("units", None)]:
            b = dict(a, **{key: value})
            result = self.demo.assess_join(a, b, keys)
            self.assertFalse(result["compatible"])
            self.assertIn(key, result["reasons"][0])

    def test_raw_snapshot_tampering_is_rejected(self):
        """A file whose bytes differ from its receipt hash is rejected."""
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            data = b"original public record"
            (folder / "record.json").write_bytes(b"changed record")
            receipts = [{"file": "record.json", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}]
            with self.assertRaisesRegex(ValueError, "snapshot"):
                self.demo.verify_snapshots(folder, receipts)

    def test_real_structures_keep_construct_mutations_and_coordinates_separate(self):
        """On the real records: EGFR 1210 / 333 / 312 residues, KRAS 188 / 170 / 168, the four construct differences, and the 1-accepted-3-rejected audit."""
        manifest, audit, projections = self.demo.build_manifest(ROOT)
        egfr, kras = manifest["targets"]
        self.assertEqual(egfr["reference_sequence"]["length"], 1210)
        self.assertEqual(egfr["structure"]["modeled_residues"], 312)
        self.assertEqual(egfr["structure"]["deposited_residues"], 333)
        self.assertEqual(kras["reference_sequence"]["isoform_id"], "P01116-2")
        self.assertEqual(kras["reference_sequence"]["length"], 188)
        self.assertEqual(kras["variant_sequence"][11], "D")
        self.assertEqual(kras["structure"]["differences_from_track_reference"], ["G12D", "C51S", "C80L", "C118S"])
        self.assertEqual(kras["structure"]["deposited_residues"], 170)
        self.assertEqual(kras["structure"]["modeled_residues"], 168)
        self.assertEqual([len(s["alpha_carbons"]) for s in projections["structures"]], [312, 168])
        self.assertEqual(manifest["bioactivity_records"], [])
        self.assertEqual([row["compatible"] for row in audit["examples"]], [True, False, False, False])

    def test_kras_isoform_link_does_not_relabel_the_prior_canonical_sequence(self):
        """Part 1's 189-residue KRAS sequence stays labelled isoform P01116-1 and differs from isoform 2B at position 151."""
        manifest, _, _ = self.demo.build_manifest(ROOT)
        link = manifest["targets"][1]["prior_episode_canonical_reference"]
        self.assertEqual(link["isoform_id"], "P01116-1")
        self.assertEqual(link["length"], 189)
        self.assertEqual(link["first_difference_from_track_isoform"], 151)

    def test_missing_assay_information_is_unknown_rather_than_a_match(self):
        """Two records that both lack a variant are NOT treated as matching."""
        result = self.demo.assess_join({"variant": None}, {"variant": None}, ("variant",))
        self.assertFalse(result["compatible"])
        self.assertIn("missing", result["reasons"][0])

    def test_repeated_builds_are_byte_identical(self):
        """Building the manifest twice gives identical bytes (the build is deterministic)."""
        first = self.demo.build_manifest(ROOT)
        second = self.demo.build_manifest(ROOT)
        self.assertEqual(self.demo.json_bytes(first), self.demo.json_bytes(second))


if __name__ == "__main__":
    unittest.main()
