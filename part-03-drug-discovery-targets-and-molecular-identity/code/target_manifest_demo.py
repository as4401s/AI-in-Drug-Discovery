"""Targets and molecular identity: build an auditable two-target manifest from frozen public records
(Part 3: "Drug Discovery Targets and Molecular Identity")

This is metadata and coordinate inspection. It is NOT docking, NOT potency prediction, NOT target
validation and NOT experimental drug discovery. Its job is to prove that the protein, the structure
and the compound we name are exactly the ones we think they are, before any later lesson uses them.

The two teaching tracks
  guided track ..... EGFR (human, UniProt P00533) with the structure 1M17 and the ligand erlotinib (AQ4)
  challenge track .. KRAS (isoform 2B, UniProt P01116-2) with the G12D change, structure 7RPZ and the
                     ligand MRTX1133 (component 6IC)

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Re-checks the size and SHA-256 hash of all 16 saved source files (UniProt, RCSB PDB, ChEMBL).
  2. Confirms each protein record: accession, gene, species and sequence length.
  3. Builds the KRAS G12D sequence from the natural isoform with a checked one-based substitution.
  4. Reads the real structure files (mmCIF), matches every residue to its UniProt position, and lists any
     differences between the crystal construct and the reference sequence.
  5. Extracts alpha-carbon and ligand coordinates actually stored in the structure files.
  6. Matches each ligand to ChEMBL by the COMPLETE InChIKey, not by name, and records why.
  7. Runs four synthetic metadata checks showing when two assay records must NOT be joined.
  8. Writes the manifest, audit, coordinates, a summary and a run receipt into data/outputs/.

WHAT YOU NEED
  * Python 3.10 or newer. Standard library only. No network access during a normal run.
  * The folder layout of this repository: code/ next to data/ (data/raw holds the saved records) and
    research/download_receipts.json.

HOW TO RUN IT
  python code/target_manifest_demo.py            (add --output-dir PATH to write somewhere else)
  python -m unittest discover -s code -p "test_target_manifest_demo.py"     (the offline checks)

WHAT YOU SHOULD SEE (values from the run shown in the video)
  2 targets, 2 reference compounds, 16 source snapshots, 0 bioactivity records
  EGFR: 1210-residue reference; structure 1M17 has 333 deposited and 312 modeled residues
  KRAS: 188-residue isoform 2B (episode 1 used the 189-residue isoform 2A); structure 7RPZ has 170
        deposited and 168 modeled residues and differs from the reference at G12D, C51S, C80L, C118S
  MRTX1133: a name search returned 8 records; the exact ligand match is CHEMBL5081048
  synthetic metadata joins: 1 accepted, 3 rejected

HOW TO READ THE RESULT
  Experimental coordinates are a model of one construct under one set of crystal conditions. A
  matching identifier is necessary evidence that two records describe the same thing, not proof that
  an experiment is comparable.
"""

# Standard library only: argparse for the command line, hashlib for hashes, shlex to split quoted mmCIF values.
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shlex
import sys
import time
from typing import Any


# ROOT is the part folder (this file lives in code/, so go one level up).
ROOT = Path(__file__).resolve().parents[1]
# The 20 standard one-letter amino-acid symbols.
AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")
# Version label written into every output so later lessons can check what they are reading.
SCHEMA_VERSION = "1.0.0"


def json_bytes(value: Any) -> bytes:
    """Serialize a value to stable JSON bytes (sorted keys, 2-space indent, trailing newline), so identical data gives an identical file hash."""
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def apply_mutation(sequence: str, position: int, original: str, replacement: str) -> str:
    """Return `sequence` with one amino acid replaced, using biological one-based positions.

    Example: apply_mutation("MAG", 2, "A", "D") gives "MDG". Position 2 must hold the stated original
    residue ("A"), both letters must be standard amino acids, and exactly one position may change.
    Anything else raises ValueError before a wrong sequence can be made.
    """
    # Check 1: the position exists (biological numbering starts at 1).
    if not 1 <= position <= len(sequence):
        raise ValueError("mutation position is outside the reference sequence")
    # Check 2: both letters are real amino acids.
    if original not in AMINO_ACIDS or replacement not in AMINO_ACIDS:
        raise ValueError("mutation must use standard one-letter amino-acid symbols")
    # Check 3: the residue at that position really is the one we say we are replacing.
    if sequence[position - 1] != original:
        raise ValueError("mutation reference residue does not match the sequence")
    # Build the new sequence: everything before, the replacement, everything after.
    mutated = sequence[: position - 1] + replacement + sequence[position:]
    # Check 4: compare old and new; exactly one position may differ.
    differences = [i + 1 for i, (before, after) in enumerate(zip(sequence, mutated)) if before != after]
    if differences != [position]:
        raise ValueError("a substitution must change exactly the selected position")
    return mutated


def verify_snapshots(raw: Path, receipts: list[dict[str, Any]]) -> None:
    """Check every saved source file against its receipt (byte count and SHA-256 hash).

    Raises ValueError if a file was changed, truncated or replaced after it was downloaded.
    """
    for receipt in receipts:
        # Read the file's bytes and compare size and hash with the receipt.
        blob = (raw / receipt["file"]).read_bytes()
        if len(blob) != receipt["bytes"] or hashlib.sha256(blob).hexdigest() != receipt["sha256"]:
            raise ValueError(f"source snapshot failed its retained identity check: {receipt['file']}")


def exact_compound(candidates: list[dict[str, Any]], inchikey: str) -> dict[str, Any]:
    """Pick the ONE ChEMBL record whose complete standard InChIKey equals `inchikey`.

    A compound name can match several records (salts, stereoisomers). The InChIKey is a hash of the exact
    structure, so requiring exactly one equal match prevents joining the wrong molecule.
    """
    # Collect every ChEMBL record whose full InChIKey equals the one from the structure database.
    matches = [
        row for row in candidates
        if (row.get("molecule_structures") or {}).get("standard_inchi_key") == inchikey
    ]
    # Zero matches or several matches are both errors; only exactly one is accepted.
    if len(matches) != 1:
        raise ValueError(f"expected exactly one complete InChIKey match; found {len(matches)}")
    return matches[0]


def assess_join(left: dict[str, Any], right: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Decide whether two records are compatible on every named context key.

    A key that is missing on either side counts as 'not a match' (missing is not evidence of agreement).
    Returns {"compatible": bool, "reasons": [...]} with a plain-language reason for every problem.
    """
    # Collect a plain-language reason for every key that blocks the join.
    reasons = []
    # Compare the two records one context key at a time.
    for key in keys:
        if left.get(key) in (None, "") or right.get(key) in (None, ""):
            reasons.append(f"{key}: missing context is not evidence of a match")
        elif left[key] != right[key]:
            reasons.append(f"{key}: {left[key]!r} differs from {right[key]!r}")
    return {"compatible": not reasons, "reasons": reasons}


def cif_loop_rows(text: str, category: str) -> list[dict[str, str]]:
    """Read the simple single-line loops used by these retained mmCIF categories.

    An mmCIF file stores tables as 'loops': a block of column names (for example _atom_site.Cartn_x)
    followed by one row of values per line. This function returns each row as a dictionary of
    {column name: value}. It is deliberately NOT a general mmCIF parser: unexpected row wrapping or
    multiline content raises an error instead of silently changing a record.
    """
    # Find the column names of the requested category (lines that start with _category.)...
    lines = text.splitlines()
    prefix = f"_{category}."
    starts = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if not starts:
        raise ValueError(f"missing mmCIF category: {category}")
    # ...read the column names, one per line...
    index = starts[0]
    tags = []
    while index < len(lines) and lines[index].startswith(prefix):
        fields = lines[index].split()
        if len(fields) != 1:
            raise ValueError(f"expected a loop for {category}")
        tags.append(fields[0].split(".", 1)[1])
        index += 1
    # ...then read one data row per line until the '#' that ends the loop, splitting quoted values correctly.
    rows = []
    while index < len(lines) and lines[index].strip() != "#":
        if lines[index].strip():
            fields = shlex.split(lines[index], comments=False, posix=True)
            if len(fields) != len(tags):
                raise ValueError(f"unexpected wrapped mmCIF row in {category}")
            rows.append(dict(zip(tags, fields)))
        index += 1
    return rows


def make_structure(raw: Path, pdb_id: str, reference: str, accession: str, ligand: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Describe one PDB structure and extract its coordinates from the saved mmCIF file.

    Arguments: the raw data folder, the PDB ID (e.g. "1M17"), the UniProt reference sequence it should
    match, the UniProt accession, and the ligand component ID (e.g. "AQ4").
    Returns (record, projection): `record` holds identity, construct and quality facts; `projection`
    holds the alpha-carbon and ligand heavy-atom coordinates in angstroms.
    """
    # Load the saved RCSB entry (experiment, resolution, revision) and polymer (sequence, alignment) records.
    entry = json.loads((raw / f"rcsb-{pdb_id}-entry.json").read_text())
    polymer = json.loads((raw / f"rcsb-{pdb_id}-polymer.json").read_text())
    # The sequence of the crystallized construct, as one string.
    sequence = polymer["entity_poly"]["pdbx_seq_one_letter_code_can"].replace("\n", "")
    # SIFTS alignment of this construct to the UniProt reference; there must be exactly one.
    alignments = [row for row in polymer["rcsb_polymer_entity_align"] if row["reference_database_accession"] == accession]
    if len(alignments) != 1:
        raise ValueError("structure does not have the expected unique UniProt alignment")
    regions = alignments[0]["aligned_regions"]
    # Walk every aligned residue: build the construct-to-reference position map and note every difference.
    differences = []
    mapping = {}
    for region in regions:
        for offset in range(region["length"]):
            entity_position = region["entity_beg_seq_id"] + offset
            reference_position = region["ref_beg_seq_id"] + offset
            mapping[entity_position] = reference_position
            before, after = reference[reference_position - 1], sequence[entity_position - 1]
            if before != after:
                differences.append(f"{before}{reference_position}{after}")
    # Read the coordinate file and keep one alpha-carbon (CA) per residue of chain A, model 1.
    cif = (raw / f"rcsb-{pdb_id}.cif").read_text()
    atoms = cif_loop_rows(cif, "atom_site")
    # If a residue has alternate positions, keep the one with higher occupancy.
    selected = {}
    for atom in atoms:
        if atom["group_PDB"] == "ATOM" and atom["label_asym_id"] == "A" and atom["label_atom_id"] == "CA" and atom["pdbx_PDB_model_num"] == "1":
            position = int(atom["label_seq_id"])
            previous = selected.get(position)
            if previous is None or float(atom["occupancy"]) > float(previous["occupancy"]):
                selected[position] = atom
    # Cross-check: the number of alpha carbons must equal the entry's count of modeled residues.
    modeled = entry["rcsb_entry_info"]["deposited_modeled_polymer_monomer_count"]
    if len(selected) != modeled:
        raise ValueError("mmCIF alpha-carbon count disagrees with the entry's modeled-residue count")
    # List every non-water molecule in the file and make sure the expected ligand is among them.
    components = sorted({a["label_comp_id"] for a in atoms if a["group_PDB"] == "HETATM" and a["label_comp_id"] != "HOH"})
    if ligand not in components:
        raise ValueError("the selected reference ligand is not present in the coordinate file")
    # Latest revision of the entry, for the record.
    revision = entry["pdbx_audit_revision_history"][-1]
    # The structure record: identity, quality, construct and the facts that stop over-interpretation.
    record = {
        "pdb_id": pdb_id, "doi": f"10.2210/pdb{pdb_id}/pdb",
        "title": entry["struct"]["title"], "polymer_entity_id": "1", "label_asym_id": "A",
        "experimental_method": entry["exptl"][0]["method"],
        "resolution_angstrom": entry["rcsb_entry_info"]["resolution_combined"][0],
        "entry_revision": f"{revision['major_revision']}.{revision['minor_revision']}",
        "entry_revision_date": revision["revision_date"],
        "deposited_residues": len(sequence), "modeled_residues": modeled,
        "unmodeled_residues": len(sequence) - modeled,
        "construct_sequence": sequence, "sifts_reference_accession": accession,
        "sifts_regions": regions, "differences_from_track_reference": differences,
        "declared_mutation": polymer["rcsb_polymer_entity"].get("pdbx_mutation"),
        "sequence_conflict_count": polymer["entity_poly"]["rcsb_conflict_count"],
        "sequence_artifact_count": polymer["entity_poly"]["rcsb_artifact_monomer_count"],
        "selected_ligand_component_id": ligand, "all_nonwater_components": components,
        "coordinate_source": f"data/raw/rcsb-{pdb_id}.cif",
        "interpretation": "experimental crystal coordinate model of this construct and conditions; not a full living receptor or a clinical outcome",
    }
    # The coordinates: alpha carbons with their reference positions, and the ligand's heavy atoms (no hydrogens).
    projection = {
        "pdb_id": pdb_id, "units": "angstrom", "source": record["coordinate_source"],
        "alpha_carbons": [
            {"entity_position": position, "reference_position": mapping.get(position),
             "author_position": atom["auth_seq_id"], "residue": atom["label_comp_id"],
             "xyz": [float(atom[f"Cartn_{axis}"]) for axis in "xyz"]}
            for position, atom in sorted(selected.items())
        ],
        "selected_ligand_heavy_atoms": [
            {"atom_id": atom["label_atom_id"], "element": atom["type_symbol"],
             "xyz": [float(atom[f"Cartn_{axis}"]) for axis in "xyz"], "occupancy": float(atom["occupancy"])}
            for atom in atoms if atom["group_PDB"] == "HETATM" and atom["label_comp_id"] == ligand and atom["type_symbol"] != "H"
        ],
    }
    return record, projection


def build_manifest(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Read all frozen inputs, run every identity check, and return (manifest, audit, projections).

    Every unexpected input (wrong species, wrong isoform, truncated record, missing ligand, ambiguous
    compound match) raises ValueError, so a broken input stops the run instead of giving a plausible manifest.
    """
    # Step 1: verify the frozen files before reading anything from them.
    raw = root / "data/raw"
    receipts = json.loads((root / "research/download_receipts.json").read_text())
    verify_snapshots(raw, receipts)
    # Small helper: read one saved JSON file from data/raw.
    def read(name: str) -> dict[str, Any]:
        return json.loads((raw / name).read_text())

    # Step 2: check each protein record (accession, human, gene name, sequence length).
    egfr = read("uniprot-P00533.json")
    kras = read("uniprot-P01116.json")
    for record, accession, gene in [(egfr, "P00533", "EGFR"), (kras, "P01116", "KRAS")]:
        if record["primaryAccession"] != accession or record["organism"]["taxonId"] != 9606 or record["genes"][0]["geneName"]["value"] != gene:
            raise ValueError("unexpected protein accession, gene or species")
        if len(record["sequence"]["value"]) != record["sequence"]["length"]:
            raise ValueError("reference sequence length disagrees with its metadata")
    # KRAS isoform 2B comes from a FASTA file; check its header.
    fasta_lines = (raw / "uniprot-P01116-2.fasta").read_text().splitlines()
    if not fasta_lines[0].startswith(">sp|P01116-2|"):
        raise ValueError("wrong KRAS isoform FASTA header")
    sequence_4b = "".join(fasta_lines[1:])
    sequence_4a = kras["sequence"]["value"]
    # Step 3: derive the G12D sequence from the isoform 2B reference with the checked substitution.
    variant_4b = apply_mutation(sequence_4b, 12, "G", "D")
    # EGFR residue 797 (index 796 in Python) must be the cysteine that covalent drugs target.
    if egfr["sequence"]["value"][796] != "C":
        raise ValueError("EGFR canonical residue 797 is not the expected cysteine")
    # Step 4: describe both structures and extract their coordinates.
    egfr_structure, egfr_projection = make_structure(raw, "1M17", egfr["sequence"]["value"], "P00533", "AQ4")
    kras_structure, kras_projection = make_structure(raw, "7RPZ", sequence_4b, "P01116", "6IC")
    # Step 5: check that ChEMBL's target records agree with UniProt (human, EGFR P00533 / KRAS P01116).
    chembl_egfr = read("chembl-CHEMBL203-target.json")
    kras_candidates = read("chembl-kras-target-search.json")["targets"]
    kras_targets = [row for row in kras_candidates if row["target_type"] == "SINGLE PROTEIN" and row["organism"] == "Homo sapiens" and [c["accession"] for c in row["target_components"]] == ["P01116"]]
    if len(kras_targets) != 1:
        raise ValueError("expected one human single-protein KRAS target")
    if chembl_egfr["organism"] != "Homo sapiens" or [row["accession"] for row in chembl_egfr["target_components"]] != ["P00533"]:
        raise ValueError("ChEMBL EGFR target components do not match UniProt")

    # Package a protein reference sequence with its hash and version, so later lessons can verify it.
    def reference(record: dict[str, Any], isoform_id: str, sequence: str, name: str) -> dict[str, Any]:
        return {"uniprot_accession": record["primaryAccession"], "isoform_id": isoform_id,
                "isoform_name": name, "organism": "Homo sapiens", "taxon_id": 9606,
                "length": len(sequence), "sequence": sequence,
                "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                "entry_version": record["entryAudit"]["entryVersion"],
                "parent_canonical_sequence_version": record["entryAudit"]["sequenceVersion"]}

    # The two targets: the guided EGFR track and the KRAS G12D challenge track.
    targets = [
        {"artifact_id": "wb.add.target.egfr.P00533-1.reference.v1", "gene": "EGFR", "track": "guided",
         "reference_sequence": reference(egfr, "P00533-1", egfr["sequence"]["value"], "1 / p170"),
         "variant": "reference", "structure": egfr_structure,
         "chembl_target_id": chembl_egfr["target_chembl_id"], "chembl_target_scope": "gene/protein-level record; assay variant still needs checking"},
        {"artifact_id": "wb.add.target.kras.P01116-2.G12D.v1", "gene": "KRAS", "track": "challenge",
         "reference_sequence": reference(kras, "P01116-2", sequence_4b, "2B / K-Ras4B"),
         "variant": "G12D", "variant_sequence": variant_4b,
         "variant_status": "locally derived single substitution of the natural isoform reference, not a new experimental sequence",
         "prior_episode_canonical_reference": {
             "uniprot_accession": "P01116", "isoform_id": "P01116-1", "isoform_name": "2A / K-Ras4A",
             "length": len(sequence_4a), "reference_residue_12": sequence_4a[11],
             "first_difference_from_track_isoform": next(i for i, (a, b) in enumerate(zip(sequence_4a, sequence_4b), 1) if a != b),
             "explanation": "episode 1 used the displayed 189-residue canonical sequence; 7RPZ explicitly specifies isoform 2B and a shorter engineered construct",
         },
         "structure": kras_structure, "chembl_target_id": kras_targets[0]["target_chembl_id"],
         "chembl_target_scope": "gene/protein-level record; this ID alone does not specify G12D or a particular assay"},
    ]
    # Step 6: match each ligand to ChEMBL by complete InChIKey (never by name alone).
    search = read("chembl-mrtx1133-search.json")["molecules"]
    compounds = []
    for name, ligand, candidates in [("erlotinib", "AQ4", [read("chembl-CHEMBL553.json")]), ("MRTX1133 (7RPZ chemical component)", "6IC", search)]:
        component = read(f"rcsb-{ligand}-chemcomp.json")
        key = component["rcsb_chem_comp_descriptor"]["InChIKey"]
        selected = exact_compound(candidates, key)
        compounds.append({
            "artifact_id": f"wb.add.compound.{ligand}.v1", "teaching_name": name,
            "pdb_component_id": ligand, "chembl_id_exact_component_match": selected["molecule_chembl_id"],
            "chembl_preferred_name": selected["pref_name"], "standard_inchi_key": key,
            "pdb_stereo_smiles": component["rcsb_chem_comp_descriptor"]["SMILES_stereo"],
            "chembl_canonical_smiles": selected["molecule_structures"]["canonical_smiles"],
            "identity_check": "exact complete standard InChIKey equality as supplied by both databases; no local chemical standardization or stereochemistry inference",
            "role": "reference record and bound component; not a newly discovered candidate or treatment recommendation",
        })
    # Name-search caution: the record called MRTX-1133 is not the exact ligand in 7RPZ (the stereochemistry differs), so both identities are kept.
    named = [row for row in search if row["pref_name"] == "MRTX-1133"]
    if len(named) != 1:
        raise ValueError("expected one preferred-name MRTX-1133 record in the retained search")
    named = named[0]
    compounds[1]["name_search_caution"] = {
        "number_of_search_results": len(search), "preferred_name_record_id": named["molecule_chembl_id"],
        "preferred_name_record_inchikey": named["molecule_structures"]["standard_inchi_key"],
        "matches_complete_pdb_inchikey": named["molecule_structures"]["standard_inchi_key"] == compounds[1]["standard_inchi_key"],
        "explanation": "the name-matched record and exact PDB-component record differ in specified stereochemistry; retain both identities rather than silently joining them",
    }
    # Step 7: four synthetic metadata checks. They show when two assay records must NOT be pooled.
    baseline = {"target": "P01116-2", "variant": "G12D", "compound": compounds[1]["standard_inchi_key"], "endpoint": "biochemical inhibition", "units": "nM"}
    examples = []
    for label, changed in [("same declared metadata", {}), ("wrong variant", {"variant": "reference G12"}), ("different biological endpoint", {"endpoint": "cell viability"}), ("unknown variant", {"variant": None})]:
        right = dict(baseline, **changed)
        examples.append({"label": label, "left": baseline, "right": right, **assess_join(baseline, right, tuple(baseline))})
    audit = {"scope": "synthetic metadata-only teaching examples, not real assays or measured potency", "examples": examples,
             "limitation": "matching these fields is necessary for this illustration, not sufficient to pool real assays; methods, construct, concentration series, exposure, controls, organism and independent replication still require curation"}
    # Step 8: assemble the manifest with scope, sources, licences and the planned hand-off to Part 4.
    manifest = {
        "schema_version": SCHEMA_VERSION, "artifact_id": "wb.add.episode03.target-compound-manifest.v1",
        "producer_episode": 3, "scope": "verified record inspection and explicit identity checks; no training, molecular prediction, new assay or potency result",
        "targets": targets, "reference_compounds": compounds, "bioactivity_records": [],
        "bioactivity_status": "not acquired or curated in this episode; dose-response and compatible assay data are the planned episode 4 handoff",
        "chembl_service_status": read("chembl-status.json"),
        "source_snapshots": receipts,
        "source_rights": {"UniProt": "CC BY 4.0; credit UniProt Consortium", "wwPDB/RCSB": "PDB archive data CC0; cite entries and original structure papers", "ChEMBL": "CC BY-SA 3.0; credit ChEMBL/EMBL-EBI and retain attribution/share-alike terms"},
    }
    projections = {"scope": "actual experimental coordinate-model values extracted from retained mmCIF; any projection is a derived view, not a measured microscope image", "structures": [egfr_projection, kras_projection]}
    return manifest, audit, projections


def main() -> None:
    """Command-line entry point: build the manifest, write every output file and the run receipt, print the summary."""
    # Optional --output-dir lets you write the results somewhere other than data/outputs.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/outputs")
    args = parser.parse_args()
    # Start a timer for the run receipt.
    started = time.perf_counter()
    manifest, audit, projections = build_manifest()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Write the three main output files.
    outputs = {"target_reference_manifest.v1.json": manifest, "compatibility_audit.json": audit, "structure_coordinates.json": projections}
    for name, value in outputs.items():
        (args.output_dir / name).write_bytes(json_bytes(value))
    # A short summary of the headline numbers; it is also printed to the screen.
    summary = {
        "schema_version": SCHEMA_VERSION, "target_count": len(manifest["targets"]), "reference_compound_count": len(manifest["reference_compounds"]),
        "source_snapshot_count": len(manifest["source_snapshots"]),
        "egfr_full_reference_residues": manifest["targets"][0]["reference_sequence"]["length"],
        "egfr_structure_deposited_residues": manifest["targets"][0]["structure"]["deposited_residues"],
        "egfr_structure_modeled_residues": manifest["targets"][0]["structure"]["modeled_residues"],
        "kras_prior_canonical_residues": manifest["targets"][1]["prior_episode_canonical_reference"]["length"],
        "kras_explicit_4b_reference_residues": manifest["targets"][1]["reference_sequence"]["length"],
        "kras_reference_residue_12": manifest["targets"][1]["reference_sequence"]["sequence"][11],
        "kras_derived_G12D_residue_12": manifest["targets"][1]["variant_sequence"][11],
        "kras_structure_deposited_residues": manifest["targets"][1]["structure"]["deposited_residues"],
        "kras_structure_modeled_residues": manifest["targets"][1]["structure"]["modeled_residues"],
        "kras_structure_reference_differences": manifest["targets"][1]["structure"]["differences_from_track_reference"],
        "mrtx1133_name_search_results": manifest["reference_compounds"][1]["name_search_caution"]["number_of_search_results"],
        "mrtx1133_exact_ligand_chembl_id": manifest["reference_compounds"][1]["chembl_id_exact_component_match"],
        "synthetic_metadata_joins_accepted": sum(row["compatible"] for row in audit["examples"]),
        "synthetic_metadata_joins_rejected": sum(not row["compatible"] for row in audit["examples"]),
        "bioactivity_records": len(manifest["bioactivity_records"]),
    }
    (args.output_dir / "results.json").write_bytes(json_bytes(summary))
    # The run receipt: time, versions, zero network calls, and hashes of this script and every output. The saved 'command' text is the one used when the receipt was produced; in this repository run  python code/target_manifest_demo.py.
    receipt = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "command": "Tools/ssd-run.sh python Playlists/ai-in-drug-discovery/3/code/target_manifest_demo.py",
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "elapsed_seconds": time.perf_counter() - started, "dependencies": "Python standard library only", "network_calls_during_run": 0,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_sha256": {name: hashlib.sha256((args.output_dir / name).read_bytes()).hexdigest() for name in [*outputs, "results.json"]},
    }
    (args.output_dir / "run_receipt.json").write_bytes(json_bytes(receipt))
    print(json_bytes(summary).decode(), end="")


if __name__ == "__main__":
    main()
