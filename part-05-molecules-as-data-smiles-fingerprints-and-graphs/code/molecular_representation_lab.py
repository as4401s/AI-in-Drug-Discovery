"""Molecules as data: an offline lab that keeps structure identity while it builds representations
(Part 5: "Molecules as Data: SMILES, Fingerprints and Graphs")

This is a teaching lab. It is NOT a trained model and it predicts nothing about activity. It shows how
a molecule written as a text string becomes checked, named numbers, and how to keep every decision visible.

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Checks that its saved inputs have not changed (file hashes) and that the results of the earlier
     lessons (Parts 3 and 4) are still the ones this lab expects.
  2. Reads 20 deliberately chosen input rows (SMILES strings): equivalent spellings of one molecule,
     different molecules, a salt, molecules with unspecified stereochemistry, and broken inputs.
  3. Parses every string with RDKit, sanitizes it, and records WHY any row fails (nothing is silently dropped).
  4. For every readable molecule it records an identity (canonical SMILES and a standard InChIKey) and a few
     descriptors (molar mass, logP, polar surface area, donors, acceptors, atom counts).
  5. Gives each row a status: accepted_primary, alias, excluded_multi_component, excluded_unspecified_stereo,
     retained_comparison or rejected.
  6. Exports each molecule as a labeled graph (atoms, bonds, adjacency matrix, 2D drawing coordinates).
  7. Builds a Morgan fingerprint (radius 2, 2048 bits) and a MACCS fingerprint for each accepted molecule,
     keeping sparse counts, folded counts and bits separate, and shows a real folding collision.
  8. Compares fingerprints with the Tanimoto coefficient (a hand example, ethanol vs dimethyl ether,
     and a lactic acid pair with and without chirality).
  9. Writes JSON and CSV files, 2D pictures and a run receipt into data/outputs/.

WHAT YOU NEED
  * Python 3.10 or newer and RDKit (see requirements.txt). No network access is used.
  * The folder layout of this repository: code/ next to data/ (data/raw holds the inputs).

HOW TO RUN IT
  python code/molecular_representation_lab.py            (add --root PATH to use another data folder)

WHAT YOU SHOULD SEE (values from the run shown in the video)
  20 audit rows -> 8 accepted_primary, 5 alias, 1 excluded_multi_component,
                   2 excluded_unspecified_stereo, 4 rejected
  ethanol vs dimethyl ether Tanimoto ... 1/9, about 0.11
  hand example Tanimoto ................ 2/4 = 0.5
  erlotinib: 48 distinct sparse identifiers -> 47 occupied bits of 2048 (one real collision),
             and 8 occupied bits in the tiny 8-bit demonstration

HOW TO READ THE RESULT
  Identifiers, descriptors and fingerprints are representations under stated rules. They are not
  measurements, and a similarity score is not a probability of shared activity.
"""
# Postponed evaluation of type hints keeps the annotations below cheap and readable.
from __future__ import annotations

# --- Imports: standard library first, then RDKit (the chemistry toolkit) ---
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import time
from typing import Any

# Chem reads and writes molecules; DataStructs holds fingerprints and compares them; rdBase has version and log tools.
from rdkit import Chem, DataStructs, rdBase
# The remaining imports are descriptor calculators, the MACCS keys, the 2D drawing helper and the Morgan generator.
from rdkit.Chem import AllChem, Crippen, Descriptors, Lipinski, MACCSkeys, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdFingerprintGenerator

# --- Fixed settings: written down once so every run (and every reader) uses the same recipe ---
# ROOT is the repository part folder: this file lives in code/, so go one level up.
ROOT = Path(__file__).resolve().parents[1]
# Version label that every saved input and output must carry.
SCHEMA = "1.0.0"
# The Morgan fingerprint recipe. Changing any value makes a different representation, so it is kept in one place:
#   radius 2          = look two bonds out from each atom
#   fpSize 2048       = fold the identifiers into a vector of 2048 positions
#   includeChirality  = let stereochemical marks change the identifiers
#   useBondTypes      = let single/double/aromatic bonds change the identifiers
#   countSimulation   = off; counts are exported separately instead
MORGAN_SETTINGS = {"radius": 2, "fpSize": 2048, "includeChirality": True,
                   "useBondTypes": True, "countSimulation": False}
# Exact InChIKeys of the two reference compounds from Part 3 (AQ4 = erlotinib, 6IC = the MRTX1133 structure component).
EXPECTED_KEYS = {"AQ4": "AAKJLRGGTJKAMG-UHFFFAOYSA-N",
                 "6IC": "SCLLZBIBSFTLIN-INOGPEIASA-N"}
# The InChIKey of the similarly named record that differs in stereochemistry (it must NOT be treated as 6IC).
NAME_ALIAS_KEY = "SCLLZBIBSFTLIN-IFMUVJFISA-N"
# Column order of the exported features.csv table.
FEATURE_COLUMNS = ["input_id", "display_name", "canonical_isomeric_smiles", "standard_inchi_key",
                   "formula", "MolWt", "MolLogP", "TPSA", "HBD", "HBA", "heavy_atoms",
                   "rotatable_bonds", "num_components", "unassigned_tetrahedral_centers"]


def json_bytes(value: Any) -> bytes:
    """Turn a Python value into JSON bytes in one fixed, sorted layout so repeated runs give identical files."""
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha(path: Path) -> str:
    """Return the SHA-256 hash of a file's bytes. A hash checks that a file is unchanged; it is not a molecular fingerprint."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_input(row: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    """Read one input row and return (audit record, molecule or None).

    Every failure gets its own status and reason, so a missing value, an empty string, a syntax error and a
    chemistry (sanitization) error are never mixed up.
    """
    # Take the raw SMILES text exactly as the row gives it.
    value = row.get("smiles")
    audit = {"input_id": row["input_id"], "raw_smiles": value}
    # A missing structure is not the same thing as a row of zeros.
    if value is None:
        return {**audit, "parse_status": "missing_input", "reason": "Missing structure is not a zero-valued feature row."}, None
    # Anything that is not text cannot be a SMILES string.
    if not isinstance(value, str):
        return {**audit, "parse_status": "invalid_input_type", "reason": "SMILES input must be text or null."}, None
    # An empty (or all-space) string is not a molecule either.
    if not value.strip():
        return {**audit, "parse_status": "empty_input", "reason": "An empty string is not an approved molecule."}, None
    # BlockLogs keeps RDKit from printing warnings; we record the problem ourselves instead.
    with rdBase.BlockLogs():
        # Step 1: parse the syntax only (sanitize=False), so a syntax error can be told apart from a chemistry error.
        molecule = Chem.MolFromSmiles(value, sanitize=False)
        if molecule is None:
            return {**audit, "parse_status": "syntax_error", "reason": "RDKit could not parse the structure syntax."}, None
        # Step 2: sanitize (check valences, aromaticity and so on); catchErrors returns a code instead of raising.
        problem = Chem.SanitizeMol(molecule, catchErrors=True)
    # A non-zero code means the string was readable but chemically invalid.
    if int(problem):
        return {**audit, "parse_status": "sanitization_error", "reason": str(problem)}, None
    # Assign stereochemistry labels (cleanIt removes marks that do not apply).
    Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
    return {**audit, "parse_status": "valid", "reason": None}, molecule


def describe(molecule: Any) -> dict[str, Any]:
    """Return the identity and the descriptors of one valid molecule as plain Python values."""
    # Find tetrahedral stereocentres; includeUnassigned=True also reports centres whose handedness was not given ("?").
    centers = Chem.FindMolChiralCenters(molecule, includeUnassigned=True, useLegacyImplementation=False)
    # The standard InChIKey is a fixed-length identifier derived from the structure.
    with rdBase.BlockLogs():
        key = Chem.MolToInchiKey(molecule)
    if not key:
        raise ValueError("Standard InChIKey could not be generated")
    return {
        # Canonical SMILES: one agreed way of writing this molecule, so equivalent spellings give the same text.
        "canonical_isomeric_smiles": Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True),
        "standard_inchi_key": key,
        # Molecular formula and average molar mass (grams per mole).
        "formula": rdMolDescriptors.CalcMolFormula(molecule),
        "MolWt": Descriptors.MolWt(molecule),
        # Crippen logP: a calculated oil-versus-water preference, not a measured solubility.
        "MolLogP": Crippen.MolLogP(molecule),
        # Topological polar surface area in square angstroms (sulfur and phosphorus left out).
        "TPSA": rdMolDescriptors.CalcTPSA(molecule, includeSandP=False),
        # Hydrogen-bond donors and acceptors as RDKit counts them.
        "HBD": Lipinski.NumHDonors(molecule),
        "HBA": Lipinski.NumHAcceptors(molecule),
        # Atom and bond counts, and how many separate pieces (a salt has more than one).
        "heavy_atoms": molecule.GetNumHeavyAtoms(),
        "rotatable_bonds": Lipinski.NumRotatableBonds(molecule),
        "num_components": len(Chem.GetMolFrags(molecule)),
        # Stereocentres whose handedness is unspecified: the strict identity table must exclude these.
        "unassigned_tetrahedral_centers": sum(label == "?" for _, label in centers),
    }


def graph_data(molecule: Any) -> dict[str, Any]:
    """Return the molecule as a labeled graph: atoms (nodes), bonds (edges) and an adjacency matrix."""
    # Separate pieces of the molecule (a salt has two or more).
    components = Chem.GetMolFrags(molecule)
    # Draw coordinates on a COPY so the atom numbering of the original is untouched.
    display = Chem.Mol(molecule)
    AllChem.Compute2DCoords(display)
    conformer = display.GetConformer()
    # These x, y pairs only make a readable picture. They are not measured positions.
    coordinates_2d = [[conformer.GetAtomPosition(i).x, conformer.GetAtomPosition(i).y]
                      for i in range(display.GetNumAtoms())]
    # Start with an all-zero square table: row i, column j will become 1 when atoms i and j are bonded.
    adjacency = [[0] * molecule.GetNumAtoms() for _ in range(molecule.GetNumAtoms())]
    # One record per atom: the node labels that travel with the adjacency matrix.
    atoms = [{"index": atom.GetIdx(), "atomic_number": atom.GetAtomicNum(), "symbol": atom.GetSymbol(),
              "formal_charge": atom.GetFormalCharge(), "aromatic": atom.GetIsAromatic(),
              "total_hydrogens": atom.GetTotalNumHs(), "chiral_tag": str(atom.GetChiralTag()),
              "cip_label": atom.GetProp("_CIPCode") if atom.HasProp("_CIPCode") else None}
             for atom in molecule.GetAtoms()]
    bonds = []
    # One record per bond (edge); also fill the adjacency matrix symmetrically.
    for bond in molecule.GetBonds():
        a, b = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        adjacency[a][b] = adjacency[b][a] = 1
        bonds.append({"index": bond.GetIdx(), "begin": a, "end": b, "type": str(bond.GetBondType()),
                      "order": bond.GetBondTypeAsDouble(), "aromatic": bond.GetIsAromatic(),
                      "stereo": str(bond.GetStereo())})
    # The "scope" fields say in plain words what this data is and is not.
    return {"num_atoms": molecule.GetNumAtoms(), "num_bonds": molecule.GetNumBonds(),
            "num_components": len(components), "component_atom_indices": [list(c) for c in components],
            "component_charges": [sum(molecule.GetAtomWithIdx(i).GetFormalCharge() for i in c) for c in components],
            "atoms": atoms, "bonds": bonds, "adjacency": adjacency,
            "display_coordinates_2d": coordinates_2d,
            "display_coordinate_scope": "RDKit 2D depiction layout on an atom-index-preserving copy, not measured positions",
            "coordinates": None, "coordinate_scope": "labeled connectivity graph; no 3D conformation or binding pose"}


def generator(fp_size: int = 2048, chirality: bool = True) -> Any:
    """Build the Morgan fingerprint generator with the recorded settings (radius 2, bond types on, count simulation off)."""
    return rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=fp_size, includeChirality=chirality,
                                                     useBondTypes=True, countSimulation=False)


def fingerprint_bundle(molecule: Any, fp_size: int = 2048, chirality: bool = True) -> dict[str, Any]:
    """Compute the Morgan fingerprint three ways (bits, folded counts, sparse counts) plus where each feature came from."""
    gen = generator(fp_size, chirality)
    # AdditionalOutput asks RDKit to also remember which atoms produced each feature.
    additional = rdFingerprintGenerator.AdditionalOutput()
    additional.CollectBitInfoMap()
    # 1) The folded bit vector: fp_size positions, each 0 or 1.
    bit_vector = gen.GetFingerprint(molecule, additionalOutput=additional)
    sparse_additional = rdFingerprintGenerator.AdditionalOutput()
    sparse_additional.CollectBitInfoMap()
    # 2) Sparse counts: the exact identifier of every environment and how often it occurs (nothing folded yet).
    sparse = gen.GetSparseCountFingerprint(molecule, additionalOutput=sparse_additional).GetNonzeroElements()
    # 3) Folded counts: counts per position after folding into fp_size positions.
    counts = gen.GetCountFingerprint(molecule).GetNonzeroElements()
    environments = []
    # For every identifier, list each (centre atom, radius) that produced it.
    for identifier, values in sorted(sparse_additional.GetBitInfoMap().items()):
        for center, radius in values:
            # The bonds inside the environment, then the atoms those bonds touch (plus the centre itself).
            bond_indices = list(Chem.FindAtomEnvironmentOfRadiusN(molecule, radius, center))
            atom_indices = {center}
            for index in bond_indices:
                bond = molecule.GetBondWithIdx(index)
                atom_indices.update([bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()])
            # Folding rule: the position is the identifier's remainder after dividing by the vector length.
            environments.append({"sparse_identifier": identifier, "folded_bit": identifier % fp_size,
                                 "center_atom": center, "radius": radius,
                                 "atom_indices": sorted(atom_indices), "bond_indices": sorted(bond_indices)})
    # Record the exact settings used for this fingerprint next to its values.
    settings = {**MORGAN_SETTINGS, "fpSize": fp_size, "includeChirality": chirality}
    return {"settings": settings, "generator_info": gen.GetInfoString(), "fp_size": len(bit_vector),
            "num_on_bits": bit_vector.GetNumOnBits(), "on_bits": list(bit_vector.GetOnBits()),
            "sparse_counts": {str(k): v for k, v in sorted(sparse.items())},
            "count_vector": {str(k): v for k, v in sorted(counts.items())},
            "bit_info_map": {str(k): [list(pair) for pair in values]
                             for k, values in sorted(additional.GetBitInfoMap().items())},
            "environments": environments,
            "scope": "Hash-based local structural summary; bits lose counts and folding can merge distinct identifiers."}


def collision_audit(molecule: Any, fp_size: int = 8) -> dict[str, Any]:
    """Find folding collisions: different sparse identifiers that land on the same position of a short vector."""
    bundle = fingerprint_bundle(molecule, fp_size)
    # bins maps each folded position to the list of distinct identifiers that landed there.
    bins: dict[int, list[int]] = defaultdict(list)
    ids = sorted(int(k) for k in bundle["sparse_counts"])
    for identifier in ids:
        bins[identifier % fp_size].append(identifier)
    # A collision needs TWO OR MORE DIFFERENT identifiers in one bin; the same identifier repeated is only repetition.
    collisions = [{"bit": bit, "sparse_ids": values} for bit, values in sorted(bins.items()) if len(values) > 1]
    # Safety check: our own modulo mapping must reproduce RDKit's on-bits exactly.
    if sorted(bins) != bundle["on_bits"]:
        raise ValueError("Observed folded bits disagree with distinct sparse-identifier modulo mapping")
    return {"fp_size": fp_size, "sparse_ids": ids, "distinct_sparse_ids": len(ids),
            "folded_on_bits": bundle["on_bits"], "collision_bins": collisions,
            "scope": "Distinct sparse identifiers mapping to one folded bin; repeated environments alone are not collision proof."}


def similarity(a: Any, b: Any) -> float:
    """Tanimoto similarity of two molecules' Morgan bit vectors: shared on-bits divided by on-bits in either."""
    gen = generator()
    return DataStructs.TanimotoSimilarity(gen.GetFingerprint(a), gen.GetFingerprint(b))


def hand_tanimoto() -> dict[str, Any]:
    """The small worked example from the video: A has positions 1, 3, 5 on and B has 1, 5, 7 on."""
    a, b = {1, 3, 5}, {1, 5, 7}
    # Two empty 8-position bit vectors, then switch the chosen positions on.
    av, bv = DataStructs.ExplicitBitVect(8), DataStructs.ExplicitBitVect(8)
    for bit in a: av.SetBit(bit)
    for bit in b: bv.SetBit(bit)
    # Shared positions (1 and 5) = 2; positions on in either (1, 3, 5, 7) = 4; so the value is 2 / 4 = 0.5.
    value = DataStructs.TanimotoSimilarity(av, bv)
    return {"a_on_bits": sorted(a), "b_on_bits": sorted(b), "intersection": len(a & b),
            "union": len(a | b), "value": value,
            "scope": "Hand-constructed binary sets, not molecular activity measurements."}


def maccs_bundle(molecule: Any) -> dict[str, Any]:
    """The MACCS fingerprint: a fixed list of structural questions instead of hashed environments."""
    fingerprint = MACCSkeys.GenMACCSKeys(molecule)
    # RDKit stores 167 positions for 166 public keys: index 0 is an unused extra position.
    return {"storage_bits": len(fingerprint), "public_key_numbers": 166,
            "on_bits": list(fingerprint.GetOnBits()),
            "scope": "RDKit public MACCS definitions; index0 unused, key1 isotope undefined; implementation conventions matter."}


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Check that the Part 3 manifest is the one this lab expects (schema, compound keys, isoforms, sequence hashes)."""
    # The schema version and artifact name must match exactly.
    if manifest.get("schema_version") != SCHEMA or manifest.get("artifact_id") != "wb.add.episode03.target-compound-manifest.v1":
        raise ValueError("Episode3 prerequisite schema/artifact identity differs")
    # Look up each reference compound by its PDB component code.
    by_component = {c["pdb_component_id"]: c for c in manifest["reference_compounds"]}
    for component, key in EXPECTED_KEYS.items():
        if by_component.get(component, {}).get("standard_inchi_key") != key:
            raise ValueError("Episode3 compound identity differs: " + component)
    # The exact ChEMBL record for each bound component must be the one we joined earlier.
    if by_component["AQ4"]["chembl_id_exact_component_match"] != "CHEMBL553" or by_component["6IC"]["chembl_id_exact_component_match"] != "CHEMBL5081048":
        raise ValueError("Episode3 exact ChEMBL component join differs")
    targets = {t["gene"]: t for t in manifest["targets"]}
    # Each target keeps its explicit isoform and variant; the stored sequence must match its recorded hash.
    for gene, isoform, variant in [("EGFR", "P00533-1", "reference"), ("KRAS", "P01116-2", "G12D")]:
        target = targets[gene]
        if target["reference_sequence"]["isoform_id"] != isoform or target["variant"] != variant:
            raise ValueError("Episode3 target isoform/variant differs")
        sequence = target["reference_sequence"]["sequence"]
        if hashlib.sha256(sequence.encode()).hexdigest() != target["reference_sequence"]["sequence_sha256"]:
            raise ValueError("Episode3 protein sequence hash disagrees")


def validate_measurement(curation: dict[str, Any]) -> dict[str, Any]:
    """Check the Part 4 curation file and return its single separately retained assay record (erlotinib IC50)."""
    if curation.get("schema_version") != SCHEMA or curation.get("artifact_id") != "wb.add.episode04.measured-activity-curation.v1":
        raise ValueError("Episode4 prerequisite schema/artifact identity differs")
    # Exactly one individual assay row is expected to be retained.
    retained = [r for r in curation["rows"] if r["curation_status"] == "retained_individual_assay_only"]
    if len(retained) != 1:
        raise ValueError("Episode4 no longer has exactly one separately retained assay")
    row = retained[0]
    # Every identifying field and the value itself must be what Part 4 saved: a join must not drift to another record.
    expected = {"activity_id": 13852013, "assay_chembl_id": "CHEMBL3095060", "molecule_chembl_id": "CHEMBL553",
                "standard_inchi_key": EXPECTED_KEYS["AQ4"], "target_chembl_id": "CHEMBL203",
                "standard_type": "IC50", "standard_relation": "=", "standard_units": "nM", "standard_value": 2.6,
                "uniprot_accession": "P00533", "variant": "reference_explicit_wild_type"}
    if any(row.get(k) != v for k, v in expected.items()):
        raise ValueError("Episode4 measurement identity, context or value differs")
    return row


def validate_prerequisites(root: Path) -> dict[str, Any]:
    """Refuse to run unless every retained input from the earlier lessons is byte-for-byte what we expect."""
    raw = root / "data/raw"
    # INPUT_LOCK.json lists the expected SHA-256 of every raw file. Compare each one.
    lock = json.loads((raw / "INPUT_LOCK.json").read_text())
    for relative, expected in lock["files"].items():
        if sha(root / relative) != expected:
            raise ValueError("Raw input snapshot hash differs: " + relative)
    # Check the retained Part 3 and Part 4 records in turn.
    manifest = json.loads((raw / "prerequisites/episode03-target_reference_manifest.v1.json").read_text())
    validate_manifest(manifest)
    curation = json.loads((raw / "prerequisites/episode04-measured_activity_curation.json").read_text())
    measurement = validate_measurement(curation)
    # "current" holds the official database records saved for this lesson; their keys must agree with the manifest.
    current = raw / "current"
    checks = []
    for component, chembl in [("AQ4", "CHEMBL553"), ("6IC", "CHEMBL5081048")]:
        molecule = json.loads((current / f"chembl-{chembl}.json").read_text())
        pdb = json.loads((current / f"rcsb-{component}-chemcomp.json").read_text())
        if molecule["molecule_structures"]["standard_inchi_key"] != EXPECTED_KEYS[component] or pdb["rcsb_chem_comp_descriptor"]["InChIKey"] != EXPECTED_KEYS[component]:
            raise ValueError("Current official database keys disagree with prerequisite")
        checks.append({"component": component, "chembl_id": chembl, "standard_inchi_key": EXPECTED_KEYS[component], "match": True})
    # The look-alike name record must keep its different key (it is NOT the 6IC component).
    name_record = json.loads((current / "chembl-CHEMBL4858364.json").read_text())
    if name_record["molecule_structures"]["standard_inchi_key"] != NAME_ALIAS_KEY:
        raise ValueError("Name-search comparison identity differs")
    # The synthetic fit from Part 4 must be unchanged too.
    fit = json.loads((raw / "prerequisites/episode04-fit_results.json").read_text())
    if fit["status"] != "accepted_for_teaching" or fit["relative_midpoint_nm"] != 9.78213223175378:
        raise ValueError("Episode4 synthetic teaching fit differs")
    return {"episode3_artifact": manifest["artifact_id"], "current_official_key_checks": checks,
            "name_record": {"chembl_id": "CHEMBL4858364", "standard_inchi_key": NAME_ALIAS_KEY,
                            "matches_6IC": False, "interpretation": "different stereochemical specification; includes unspecified centers, not a proven opposite stereoisomer"},
            "episode4_synthetic_midpoint_nm": fit["relative_midpoint_nm"],
            "episode4_raw_rows": curation["acquired_source_row_count"], "episode4_selected_cases": len(curation["rows"]),
            "separate_measured_record": measurement, "training_ready": False,
            "scope": "Consumer validation of retained prior schemas/identities; no new assay, fit or biological label is derived."}


def build_payload(root: Path = ROOT) -> dict[str, Any]:
    """Run the whole lab in memory and return one dictionary holding every result."""
    # Step 1: prerequisites must pass before anything is computed.
    prerequisites = validate_prerequisites(root)
    inputs = json.loads((root / "data/raw/representation_inputs.json").read_text())
    if inputs["schema_version"] != SCHEMA or inputs["artifact_id"] != "wb.add.episode05.representation-inputs.v1":
        raise ValueError("Representation input schema/artifact identity differs")
    # Containers for the results; the "seen" sets catch duplicate row IDs and duplicate molecular identities.
    audits, features, graphs, fingerprints, molecules = [], [], {}, {}, {}
    seen_inputs: set[str] = set()
    seen_primary: set[str] = set()
    # Step 2: go through the 20 input rows one by one. No row is ever dropped without a recorded status.
    for row in inputs["inputs"]:
        identity = row["input_id"]
        if identity in seen_inputs:
            raise ValueError("Duplicate input row ID")
        seen_inputs.add(identity)
        audit, molecule = parse_input(row)
        audit.update({"display_name": row["display_name"], "source_id": row["source_id"], "role": row["role"]})
        # Unreadable rows are rejected, with the reason already stored in the audit record.
        if molecule is None:
            audit["matrix_status"] = "rejected"
            audits.append(audit)
            continue
        # Readable rows get an identity and descriptors.
        description = describe(molecule)
        audit.update(description)
        # If the row names an exact InChIKey from an official source, RDKit must reproduce it.
        expected_key = row.get("expected_standard_inchi_key")
        if expected_key and description["standard_inchi_key"] != expected_key:
            raise ValueError("RDKit result disagrees with exact source InChIKey: " + identity)
        molecules[identity] = molecule
        graphs[identity] = graph_data(molecule)
        # Status 1: an alias is a different spelling of a molecule we already hold. It must recover the SAME structure.
        if row["role"] == "alias":
            parent = next((a for a in audits if a["input_id"] == row["alias_of"]), None)
            if parent is None or parent.get("canonical_isomeric_smiles") != description["canonical_isomeric_smiles"] or parent.get("standard_inchi_key") != description["standard_inchi_key"]:
                raise ValueError("Declared alias does not recover the same exact structure: " + identity)
            audit.update({"matrix_status": "alias", "alias_of": row["alias_of"]})
        # Status 2: our strict policy keeps single-component molecules only (salts are excluded, not deleted).
        elif description["num_components"] != 1:
            audit["matrix_status"] = "excluded_multi_component"
        # Status 3: our strict identity policy excludes molecules with unspecified stereocentres.
        elif description["unassigned_tetrahedral_centers"]:
            audit["matrix_status"] = "excluded_unspecified_stereo"
        # Status 4: approved rows enter the main matrix, once per distinct molecular identity.
        elif row["main_matrix_approved"]:
            if description["standard_inchi_key"] in seen_primary:
                raise ValueError("Duplicate approved molecular identity")
            seen_primary.add(description["standard_inchi_key"])
            audit["matrix_status"] = "accepted_primary"
            features.append({"input_id": identity, "display_name": row["display_name"], **description})
            fingerprints[identity] = {"morgan": fingerprint_bundle(molecule), "maccs": maccs_bundle(molecule)}
        # Anything else is kept for comparison only.
        else:
            audit["matrix_status"] = "retained_comparison"
        audits.append(audit)
    # Step 3: similarity between every pair of accepted molecules (a square table).
    primary_ids = [r["input_id"] for r in features]
    pairwise = [[similarity(molecules[a], molecules[b]) for b in primary_ids] for a in primary_ids]
    # Step 4: the lactic acid pair. Compare their SMILES with and without stereo marks, and their fingerprints with
    # and without chirality, to show what each setting keeps or loses.
    stereo = {"a_input": "lactic-at", "b_input": "lactic-aat",
              "isomeric_smiles": [Chem.MolToSmiles(molecules[i], isomericSmiles=True) for i in ["lactic-at", "lactic-aat"]],
              "nonisomeric_smiles": [Chem.MolToSmiles(molecules[i], isomericSmiles=False) for i in ["lactic-at", "lactic-aat"]],
              "chiral_tanimoto": similarity(molecules["lactic-at"], molecules["lactic-aat"]),
              "achiral_tanimoto": DataStructs.TanimotoSimilarity(generator(chirality=False).GetFingerprint(molecules["lactic-at"]), generator(chirality=False).GetFingerprint(molecules["lactic-aat"]))}
    # Step 5: assemble everything, with the settings and the scope (what the numbers do NOT mean) written beside it.
    return {"schema_version": SCHEMA, "artifact_id": "wb.add.episode05.representation-lab.v1",
            "producer_episode": 5, "rdkit_version": rdBase.rdkitVersion,
            "scope": "Eight approved unique single-component chemical identities represented locally; teaching features only, no trained model or training-ready activity dataset.",
            "settings": {"morgan": MORGAN_SETTINGS, "canonicalization": "RDKit canonical=True,isomericSmiles=True; toolkit/version specific",
                         "standardization": "No neutralization, largest-fragment selection, tautomer normalization or stereo removal.",
                         "descriptors": {"MolWt": "average molecular mass, g/mol", "MolLogP": "Wildman-Crippen calculated logP, dimensionless; not experimental solubility",
                                         "TPSA": "calculated topological polar surface area, angstrom squared; includeSandP=False",
                                         "HBD": "RDKit hydrogen-bond donor count", "HBA": "RDKit hydrogen-bond acceptor count",
                                         "heavy_atoms": "non-hydrogen atom count", "rotatable_bonds": "RDKit Lipinski.NumRotatableBonds default definition"},
                         "graph": "Heavy-atom SMILES graph with H counts and stereo attributes, no 3D coordinates",
                         "training_ready": False, "activity_labels_in_features": False},
            "prerequisites": prerequisites, "input_audit": audits, "features": features,
            "matrix_status_counts": dict(sorted(Counter(a["matrix_status"] for a in audits).items())),
            "graphs": graphs, "fingerprints": fingerprints, "hand_tanimoto": hand_tanimoto(),
            "pairwise_tanimoto": {"input_ids": primary_ids, "values": pairwise,
                                   "scope": "Binary Morgan similarity for the declared settings; not potency, efficacy or target binding."},
            "ethanol_ether_tanimoto": similarity(molecules["ethanol"], molecules["dimethyl-ether"]),
            "stereo_comparison": stereo,
            "collision_demo": {"input_id": "erlotinib", **collision_audit(molecules["erlotinib"], 8)},
            "collision_at_2048": {"input_id": "erlotinib", **collision_audit(molecules["erlotinib"], 2048)},
            "notes": ["InChIKey and canonical SMILES are identifiers/representations, not biological measurements.",
                      "SELFIES and SAFE are source-based overviews only; their packages are not installed or executed.",
                      "MACCS differs from Morgan: predefined public keys versus hashed circular environments.",
                      "All20 inputs survive in audit; multi-component and unspecified-stereo examples are retained separately."]}


def export_payload(payload: dict[str, Any], output: Path) -> dict[str, str]:
    """Write the JSON and CSV result files and return the SHA-256 of each one."""
    output.mkdir(parents=True, exist_ok=True)
    # One JSON file per result group, written with the fixed layout from json_bytes().
    files = {"lesson_payload.json": payload, "input_audit.json": payload["input_audit"],
             "graphs.json": payload["graphs"], "fingerprints.json": payload["fingerprints"],
             "representation_settings.json": payload["settings"], "identity_audit.json": payload["prerequisites"]}
    for name, value in files.items(): (output / name).write_bytes(json_bytes(value))
    # features.csv: one row per accepted molecule, columns in FEATURE_COLUMNS order.
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=FEATURE_COLUMNS, lineterminator="\n")
    writer.writeheader(); writer.writerows(payload["features"])
    (output / "features.csv").write_text(text.getvalue())
    # morgan_bits.csv (2048 columns) and maccs_bits.csv (167 columns): the folded bit vectors as 0/1 tables.
    for kind, size in [("morgan", 2048), ("maccs", 167)]:
        text = io.StringIO(newline="")
        writer = csv.writer(text, lineterminator="\n")
        writer.writerow(["input_id"] + [f"bit_{i}" for i in range(size)])
        for row in payload["features"]:
            bits = set(payload["fingerprints"][row["input_id"]][kind]["on_bits"])
            writer.writerow([row["input_id"]] + [int(i in bits) for i in range(size)])
        (output / f"{kind}_bits.csv").write_text(text.getvalue())
    # The receipt (written later in main) is left out of this hash list, because it contains the list.
    return {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file() and path.name != "run_receipt.json"}


def export_depictions(payload: dict[str, Any], output: Path) -> dict[str, str]:
    """Draw a 2D picture (SVG) of every readable molecule and return the SHA-256 of each file."""
    output.mkdir(parents=True, exist_ok=True)
    for row in payload["input_audit"]:
        # Rows that could not be parsed have no molecule to draw.
        if row["parse_status"] != "valid": continue
        molecule = Chem.MolFromSmiles(row["canonical_isomeric_smiles"])
        AllChem.Compute2DCoords(molecule)
        # A 720 x 420 pixel SVG canvas; addStereoAnnotation prints the R/S labels where they are defined.
        drawer = rdMolDraw2D.MolDraw2DSVG(720, 420)
        drawer.drawOptions().addStereoAnnotation = True
        drawer.DrawMolecule(molecule)
        drawer.FinishDrawing()
        (output / f"{row['input_id']}.svg").write_text(drawer.GetDrawingText())
    return {path.name: sha(path) for path in sorted(output.glob("*.svg"))}


def main() -> None:
    """Run the lab, save every output with a run receipt, and print a short summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    # --root lets you point the script at a different folder that has the same data/raw layout.
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    start = time.monotonic()
    payload = build_payload(args.root)
    output = args.root / "data/outputs"
    hashes = export_payload(payload, output)
    depictions = export_depictions(payload, output / "depictions")
    # The receipt records how and when this run happened. "command" is a log of how the original run was started
    # on the author's machine; it is not used when you run the script yourself.
    receipt = {"generated_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.monotonic() - start,
               "command": "Tools/ssd-run.sh exec Runtime/python-chem/bin/python Playlists/ai-in-drug-discovery/5/code/molecular_representation_lab.py",
               "python": platform.python_version(), "platform": platform.platform(), "rdkit": rdBase.rdkitVersion,
               "code_sha256": sha(Path(__file__)), "input_lock_sha256": sha(args.root / "data/raw/INPUT_LOCK.json"),
               "outputs": hashes, "depictions": depictions, "network_calls_required": 0,
               "scope": "Actual local deterministic chemistry run; no activity model fitting or new biological experiment."}
    (output / "run_receipt.json").write_bytes(json_bytes(receipt))
    # Print the headline numbers so you can compare them with the video.
    print(json.dumps({"features": len(payload["features"]), "audit_rows": len(payload["input_audit"]),
                      "matrix_status_counts": payload["matrix_status_counts"], "ethanol_ether_tanimoto": payload["ethanol_ether_tanimoto"],
                      "stereo": payload["stereo_comparison"], "tiny_collision_bins": len(payload["collision_demo"]["collision_bins"]),
                      "collision_bins_at_2048": len(payload["collision_at_2048"]["collision_bins"]), "receipt": str(output / "run_receipt.json")}, indent=2))


if __name__ == "__main__":
    main()
