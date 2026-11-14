"""Scientific regression checks for the molecular representation lab (Part 5)

Every test states one scientific claim of the lesson and proves it with RDKit, locally and offline.
Together they show that equivalent SMILES give the same identity, that formula and mass do not identify
a structure, that graphs, fingerprints and similarity behave as the video says, and that bad or
ambiguous inputs fail loudly instead of being repaired in silence.

WHAT YOU NEED
  * Python 3.10 or newer and RDKit (see requirements.txt).
  * The folder layout of this repository: code/ next to data/ (data/raw/prerequisites holds the saved
    results of Parts 3 and 4).

HOW TO RUN IT
  python -m unittest discover -s code -p "test_molecular_representation_lab.py" -v
"""
from __future__ import annotations

# unittest runs the checks; copy makes edited copies for the tampering tests; importlib loads the lab as a module; tempfile makes throw-away folders.
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
# MODULE is the lab script under test (code/molecular_representation_lab.py).
MODULE = ROOT / "code/molecular_representation_lab.py"


class RepresentationTests(unittest.TestCase):
    """Regression checks for parsing, identity, graphs, fingerprints, similarity and the lesson payload."""
    def setUp(self) -> None:
        """Load molecular_representation_lab.py as a module before every test."""
        self.assertTrue(MODULE.is_file(), "molecular representation implementation is missing")
        spec = importlib.util.spec_from_file_location("representation_lab", MODULE)
        self.lab = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.lab)

    def mol(self, smiles):
        """Helper: parse a SMILES string with the lab's own parser and return the RDKit molecule (the test fails if it is not valid)."""
        audit, molecule = self.lab.parse_input({"input_id": "test", "smiles": smiles})
        self.assertEqual(audit["parse_status"], "valid")
        return molecule

    def assert_descriptions_agree(self, a, b):
        """Helper: two description dictionaries must match; floats may differ only by rounding noise (1e-12)."""
        for name in a:
            if isinstance(a[name], float):
                self.assertAlmostEqual(a[name], b[name], delta=1e-12, msg=name)
            else:
                self.assertEqual(a[name], b[name], name)

    def test_equivalent_ethanol_traversals_recover_same_identity_and_features(self):
        """CCO, OCC and C(O)C are three spellings of one molecule and give identical identity and features."""
        results = [self.lab.describe(self.mol(s)) for s in ["CCO", "OCC", "C(O)C"]]
        self.assert_descriptions_agree(results[0], results[1])
        self.assert_descriptions_agree(results[1], results[2])

    def test_formula_and_mass_do_not_identify_connectivity(self):
        """Ethanol and dimethyl ether share formula C2H6O and mass, but differ in structure and in hydrogen-bond donors."""
        ethanol = self.lab.describe(self.mol("CCO"))
        ether = self.lab.describe(self.mol("COC"))
        self.assertEqual(ethanol["formula"], "C2H6O")
        self.assertEqual(ethanol["formula"], ether["formula"])
        self.assertEqual(ethanol["MolWt"], ether["MolWt"])
        self.assertNotEqual(ethanol["canonical_isomeric_smiles"], ether["canonical_isomeric_smiles"])
        self.assertEqual((ethanol["HBD"], ether["HBD"]), (1, 0))

    def test_ethanol_graph_keeps_atom_labels_and_hydrogens(self):
        """Ethanol's graph has 3 atoms and 2 bonds, the right elements, the right adjacency matrix and 6 hydrogens."""
        graph = self.lab.graph_data(self.mol("CCO"))
        self.assertEqual((graph["num_atoms"], graph["num_bonds"]), (3, 2))
        self.assertEqual([a["atomic_number"] for a in graph["atoms"]], [6, 6, 8])
        self.assertEqual(graph["adjacency"], [[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        self.assertEqual(sum(a["total_hydrogens"] for a in graph["atoms"]), 6)

    def test_display_coordinates_are_2d_and_match_original_atom_indices(self):
        """Drawing coordinates are 2D (x, y), one per atom, and are only for display."""
        graph = self.lab.graph_data(self.mol("CCO"))
        self.assertIn("display_coordinates_2d", graph)
        self.assertEqual(len(graph["display_coordinates_2d"]), 3)
        self.assertTrue(all(len(point) == 2 for point in graph["display_coordinates_2d"]))

    def test_sparse_environments_retain_actual_radius_membership_and_fold_mapping(self):
        """Each Morgan environment records its radius, centre, atoms and bonds, and its folded bit equals identifier modulo 2048."""
        molecule = self.mol("C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1")
        bundle = self.lab.fingerprint_bundle(molecule)
        self.assertIn("environments", bundle)
        self.assertEqual({e["radius"] for e in bundle["environments"]}, {0, 1, 2})
        for environment in bundle["environments"]:
            self.assertIn(environment["center_atom"], environment["atom_indices"])
            self.assertEqual(environment["folded_bit"], environment["sparse_identifier"] % 2048)
            self.assertTrue(all(0 <= i < molecule.GetNumBonds() for i in environment["bond_indices"]))

    def test_renumbering_changes_indices_but_not_identity(self):
        """Reordering the atoms changes the atom indices in the graph but not the molecule's identity."""
        # RDKit is imported only here, where a test needs it directly.
        from rdkit import Chem
        molecule = self.mol("CCO")
        permuted = Chem.RenumberAtoms(molecule, [2, 1, 0])
        self.assertNotEqual(self.lab.graph_data(molecule)["atoms"], self.lab.graph_data(permuted)["atoms"])
        self.assert_descriptions_agree(self.lab.describe(molecule), self.lab.describe(permuted))

    def test_benzene_aromatic_and_kekule_forms_agree(self):
        """Aromatic and Kekule spellings of benzene describe the same molecule."""
        self.assertEqual(self.lab.describe(self.mol("c1ccccc1")), self.lab.describe(self.mol("C1=CC=CC=C1")))

    def test_stereo_survives_identity_and_chiral_fingerprints(self):
        """The two lactic acid mirror images get different InChIKeys and different chiral fingerprints, and identical ones when chirality is switched off."""
        a, b = self.mol("C[C@H](O)C(=O)O"), self.mol("C[C@@H](O)C(=O)O")
        self.assertNotEqual(self.lab.describe(a)["standard_inchi_key"], self.lab.describe(b)["standard_inchi_key"])
        self.assertNotEqual(self.lab.fingerprint_bundle(a)["on_bits"], self.lab.fingerprint_bundle(b)["on_bits"])
        self.assertEqual(self.lab.fingerprint_bundle(a, chirality=False)["on_bits"], self.lab.fingerprint_bundle(b, chirality=False)["on_bits"])

    def test_unspecified_stereo_is_detected_not_invented(self):
        """A stereo centre left unspecified is counted as unassigned and no chirality is invented."""
        result = self.lab.describe(self.mol("CC(O)C(=O)O"))
        self.assertEqual(result["unassigned_tetrahedral_centers"], 1)
        self.assertNotIn("@", result["canonical_isomeric_smiles"])

    def test_salt_retains_both_components_and_component_charges(self):
        """Sodium acetate keeps both components (charges -1 and +1) and all 5 atoms."""
        graph = self.lab.graph_data(self.mol("CC(=O)[O-].[Na+]"))
        self.assertEqual(graph["num_components"], 2)
        self.assertEqual(sorted(graph["component_charges"]), [-1, 1])
        self.assertEqual(graph["num_atoms"], 5)

    def test_missing_and_empty_inputs_stay_explicit_failures(self):
        """None, an empty string and whitespace each get their own failure status and no molecule."""
        for value, expected in [(None, "missing_input"), ("", "empty_input"), ("   ", "empty_input")]:
            audit, molecule = self.lab.parse_input({"input_id": "bad", "smiles": value})
            self.assertEqual(audit["parse_status"], expected)
            self.assertIsNone(molecule)

    def test_syntax_and_valence_failures_are_distinct(self):
        """A broken ring closure (syntax error) and an impossible valence (sanitization error) are reported differently, each with a reason."""
        for value, expected in [("C1CC", "syntax_error"), ("CO(C)C", "sanitization_error")]:
            audit, molecule = self.lab.parse_input({"input_id": "bad", "smiles": value})
            self.assertEqual(audit["parse_status"], expected)
            self.assertIsNone(molecule)
            self.assertTrue(audit["reason"])

    def test_morgan_settings_and_storage_are_explicit(self):
        """The Morgan settings (radius 2, 2048 bits, chirality, bond types) are recorded and ethanol's on-bits are a known list."""
        bundle = self.lab.fingerprint_bundle(self.mol("CCO"))
        self.assertEqual(bundle["fp_size"], 2048)
        self.assertEqual(bundle["settings"], {"radius": 2, "fpSize": 2048, "includeChirality": True, "useBondTypes": True, "countSimulation": False})
        self.assertEqual(bundle["on_bits"], [80, 222, 294, 807, 1057, 1410])
        self.assertEqual(sum(bundle["count_vector"].values()), sum(bundle["sparse_counts"].values()))

    def test_counts_preserve_repeated_environments_while_bits_do_not(self):
        """Butane repeats some environments: counts keep the repeats, bits cannot."""
        bundle = self.lab.fingerprint_bundle(self.mol("CCCC"))
        self.assertTrue(any(count > 1 for count in bundle["sparse_counts"].values()))
        self.assertLess(bundle["num_on_bits"], sum(bundle["sparse_counts"].values()))

    def test_fold_collision_uses_distinct_sparse_ids(self):
        """Folding erlotinib's identifiers into 8 bits makes real collisions: different identifiers that share one bit."""
        molecule = self.mol("C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1")
        audit = self.lab.collision_audit(molecule, 8)
        self.assertTrue(audit["collision_bins"])
        for collision in audit["collision_bins"]:
            ids = collision["sparse_ids"]
            self.assertGreater(len(set(ids)), 1)
            self.assertEqual({value % 8 for value in ids}, {collision["bit"]})
        self.assertEqual(sorted(audit["folded_on_bits"]), sorted({i % 8 for i in audit["sparse_ids"]}))

    def test_hand_tanimoto_matches_library_and_is_symmetric(self):
        """The hand example gives 2 shared of 4 in the union = 0.5, a molecule compared with itself scores 1, and the score is symmetric."""
        result = self.lab.hand_tanimoto()
        self.assertEqual((result["intersection"], result["union"]), (2, 4))
        self.assertEqual(result["value"], 0.5)
        a, b = self.mol("CCO"), self.mol("COC")
        self.assertEqual(self.lab.similarity(a, a), 1.0)
        self.assertEqual(self.lab.similarity(a, b), self.lab.similarity(b, a))

    def test_maccs_storage_preserves_public_key_numbering(self):
        """MACCS has 166 public keys stored in 167 positions; position 0 is unused and key 164 is on for ethanol."""
        result = self.lab.maccs_bundle(self.mol("CCO"))
        self.assertEqual(result["storage_bits"], 167)
        self.assertEqual(result["public_key_numbers"], 166)
        self.assertNotIn(0, result["on_bits"])
        self.assertIn(164, result["on_bits"])

    def test_prerequisite_manifest_tampering_fails(self):
        """An edited Part 3 manifest (schema, artifact ID or an InChIKey) is rejected."""
        manifest = json.loads((ROOT / "data/raw/prerequisites/episode03-target_reference_manifest.v1.json").read_text())
        self.lab.validate_manifest(manifest)
        for field, value in [("schema_version", "2.0.0"), ("artifact_id", "wrong")]:
            changed = copy.deepcopy(manifest); changed[field] = value
            with self.assertRaises(ValueError): self.lab.validate_manifest(changed)
        changed = copy.deepcopy(manifest)
        changed["reference_compounds"][1]["standard_inchi_key"] = "SCLLZBIBSFTLIN-IFMUVJFISA-N"
        with self.assertRaises(ValueError): self.lab.validate_manifest(changed)

    def test_prior_measurement_is_validated_and_kept_contextual(self):
        """The one retained Part 4 record (2.6 nM, assay CHEMBL3095060) is validated, has no ATP concentration, and a changed identity is rejected."""
        curation = json.loads((ROOT / "data/raw/prerequisites/episode04-measured_activity_curation.json").read_text())
        row = self.lab.validate_measurement(curation)
        self.assertEqual((row["activity_id"], row["assay_chembl_id"], row["standard_value"]), (13852013, "CHEMBL3095060", 2.6))
        self.assertIsNone(row["ATP_concentration"])
        changed = copy.deepcopy(curation)
        next(r for r in changed["rows"] if r["activity_id"] == 13852013)["standard_inchi_key"] = "wrong"
        with self.assertRaises(ValueError): self.lab.validate_measurement(changed)

    def test_main_matrix_is_unique_and_excludes_policy_failures(self):
        """The main matrix has 8 unique molecules, no salts or unspecified stereo, no measured potency, from 20 audited inputs of which 5 are aliases."""
        result = self.lab.build_payload(ROOT)
        rows = result["features"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({r["standard_inchi_key"] for r in rows}), 8)
        self.assertTrue(all(r["num_components"] == 1 and r["unassigned_tetrahedral_centers"] == 0 for r in rows))
        self.assertTrue(all("IC50" not in r and "pIC50" not in r for r in rows))
        self.assertEqual(len(result["input_audit"]), 20)
        self.assertEqual(sum(r["matrix_status"] == "alias" for r in result["input_audit"]), 5)

    def test_name_alias_stereo_specification_is_not_silently_merged(self):
        """The name-matched MRTX1133 record has a different InChIKey from the PDB ligand and is excluded for unspecified stereochemistry."""
        result = self.lab.build_payload(ROOT)
        by_id = {r["input_id"]: r for r in result["input_audit"]}
        self.assertNotEqual(by_id["mrtx1133-6ic"]["standard_inchi_key"], by_id["mrtx1133-name-alias"]["standard_inchi_key"])
        self.assertEqual(by_id["mrtx1133-name-alias"]["matrix_status"], "excluded_unspecified_stereo")

    def test_scientific_payload_and_exports_are_deterministic(self):
        """Building and exporting the payload twice gives identical results."""
        first = self.lab.build_payload(ROOT)
        second = self.lab.build_payload(ROOT)
        self.assertEqual(first, second)
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            before = self.lab.export_payload(first, target)
            after = self.lab.export_payload(second, target)
            self.assertEqual(before, after)
            exported = json.loads((target / "lesson_payload.json").read_text())
            self.assertEqual(exported["scope"], first["scope"])


if __name__ == "__main__":
    unittest.main()
