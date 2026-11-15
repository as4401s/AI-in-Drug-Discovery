#!/usr/bin/env python3
"""worked_examples.py - the small calculations from Part 3 of the video, reproduced step by step.

What it does
    The video builds each hard idea from an everyday picture and a tiny example with numbers you can repeat on a
    calculator. This script runs the same examples in the same order, so you can check every number and then change
    the inputs. The last examples use the real records saved in `data/`, with the real functions of
    `target_manifest_demo.py`.

      Part 1 - from observation to a target
        1.  Target and outcome:    growth of a dish of cells with and without a blocking molecule
        2.  Association:           two rows of numbers that rise together, and a protein level in two cell types
        3.  Intervention:          control, knock-down, a second tool and a rescue
        4.  Validation:            one cell line against three patient samples
        5.  The screening funnel:  ten thousand molecules down to thirty-two confirmed hits
        6.  Early negative results: what a cheap early test saves
        7.  The role of a model:   one sentence that names object, quantity, assay and conditions
      Part 2 - can a molecule change it?
        8.  Occupancy:             fraction occupied = concentration / (concentration + KD)
        9.  Affinity and potency:  the same molecule in a test tube and in cells
        10. Selectivity:           ratios, and occupancy at one dose
        11. Exposure:              a half-life, the time above a useful level, and what reaches the target
        12. The evidence ladder:   which claim each number supports
      Part 3 - our two targets
        13. Phosphate counts:      ATP to ADP, GTP to GDP
        14. Reading G12D:          seat twelve, index eleven
        15. Hashes:                one letter apart, two unrelated fingerprints
        16. Isoforms:              189 against 188 amino acids, and where they first differ
        17. Structure counts:      deposited against modeled, resolution, and the numbering shift
      Part 4 - connect the evidence (the program)
        18. The sequence check:    the four checks of apply_mutation
        19. Coordinates:           the distance between two neighbouring alpha carbons
        20. Chemical identity:     the three blocks of an InChIKey and the exact match
        21. Rejecting a join:      the four synthetic metadata checks
        22. Units and endpoints:   0.2 micromolar is 200 nanomolar, and a blended mean
        23. Missing values:        skip the empty cell or turn it into a zero

What it needs
    Python 3.10 or newer and the standard library only. Nothing is downloaded. Examples 16, 17, 19 and 20 read the
    saved files in `data/`, and examples 14, 18, 20 and 21 call functions of `target_manifest_demo.py`, so run the
    script from the folder that holds `code/` and `data/`.

What to expect
    The numbers printed below match the video (rounded):
      growth 800 -> 300 (a drop of 62.5 %)              funnel 10000 -> 120 -> 70 -> 35 -> 32
      occupancy at KD = 10 nM: 9.1 %, 50 %, 90.9 %, 99.0 %    selectivity 5 fold and 500 fold
      useful exposure of about 7 hours                    MTEYKLVVVGAG -> MTEYKLVVVGAD
      KRAS isoforms first differ at position 151          alpha carbon spacing 3.81 angstrom
      InChIKey blocks of 14, 10 and 1 characters          metadata joins: 1 accepted, 3 rejected
      mean 19.0 (skip the empty cell) against 14.25 (empty cell turned into zero)

Run it:
    python code/worked_examples.py
"""
import hashlib
import json
import math
import sys
from pathlib import Path

# The folder that holds `code/` and `data/`. The real functions of the video's program are imported from it.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from target_manifest_demo import apply_mutation, assess_join, exact_compound  # noqa: E402


def heading(number: int, title: str) -> None:
    """Print one numbered heading so the output is easy to match with the video."""
    print(f"{number}. {title}")


# ----------------------------------------------------------------------------------------------------- Part 1
def target_and_outcome() -> None:
    """A dish holds 1000 cells. Without the molecule it grows to 1800; with it, to 1300."""
    heading(1, "Target and outcome: growth with and without a molecule that blocks a receptor")
    start = 1000
    untreated_end, treated_end = 1800, 1300
    growth_untreated = untreated_end - start   # 800 new cells in one day
    growth_treated = treated_end - start       # 300 new cells in one day
    drop = (growth_untreated - growth_treated) / growth_untreated
    print(f"   growth without the molecule: {growth_untreated}, with it: {growth_treated}")
    print(f"   the growth fell by {drop:.1%}, which is more than half")
    print("   the receptor is the target (where we act); the growth is the outcome (what we measure)\n")


def association() -> None:
    """Two rows that rise together form an association; a third factor (sunshine) can drive both."""
    heading(2, "Association: ice cream, sunburn and a protein level")
    ice_cream = [20, 35, 50, 60, 80, 90]
    sunburn = [2, 4, 5, 7, 9, 10]
    # Pearson correlation: +1 means the two rows rise and fall perfectly together
    n = len(ice_cream)
    mean_x, mean_y = sum(ice_cream) / n, sum(sunburn) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(ice_cream, sunburn))
    spread_x = math.sqrt(sum((x - mean_x) ** 2 for x in ice_cream))
    spread_y = math.sqrt(sum((y - mean_y) ** 2 for y in sunburn))
    print(f"   ice cream {ice_cream}  sunburn {sunburn}")
    print(f"   correlation = {cov / (spread_x * spread_y):.3f}: a strong association, and hot sunny days drive both")
    print("   protein level: 5 units in aggressive cells, 2 units in calm cells")
    print("   three stories fit: the protein drives the behavior, the behavior raises the protein, or a third process raises both\n")


def intervention() -> None:
    """Control, knock-down, a second tool, and a rescue: the effect follows the protein."""
    heading(3, "Intervention: switching a gene down and adding the protein back")
    control, knockdown, second_tool, rescue = 100, 55, 58, 92
    print(f"   growth score: control {control}, protein reduced {knockdown}, second tool {second_tool}, protein returned {rescue}")
    print(f"   the first tool lowers the score by {control - knockdown} points; the second tool gives a similar value ({second_tool})")
    print("   the rescue brings the score back up, so the effect follows the protein: converging evidence\n")


def validation() -> None:
    """A result in one engineered cell line, compared with three patient samples."""
    heading(4, "Validation: where does the result apply?")
    cell_line = 50                       # percent slowing of growth
    patients = [48, 12, 0]
    mean_patients = sum(patients) / len(patients)
    print(f"   engineered cell line: {cell_line} % slowing; three patient samples: {patients}")
    print(f"   the mean of the three patient samples is {mean_patients:.0f} %, much smaller than {cell_line} %\n")


def screening_funnel() -> None:
    """Ten thousand molecules, four questions, thirty-two confirmed hits."""
    heading(5, "The screening funnel: each round answers a new question")
    tested = 10_000
    initial_hits = 120
    confirmed = 70
    removed_by_counter_assay = 35
    after_counter_assay = confirmed - removed_by_counter_assay      # 35
    wrong_identity = 3
    final_hits = after_counter_assay - wrong_identity               # 32
    print(f"   tested {tested}, initial hits {initial_hits}, confirmed by retest {confirmed}")
    print(f"   after the counter-assay {after_counter_assay}, after the identity check {final_hits}")
    print(f"   the first list was {initial_hits / final_hits:.2f} times longer than the final one (almost four times)\n")


def early_negative_result() -> None:
    """Three stages that cost 1, 10 and 100 units: a clean early 'no' is cheap."""
    heading(6, "A well-designed negative result: the cost of finding out late")
    stage_costs = [1, 10, 100]
    total = sum(stage_costs)
    print(f"   running every stage costs {total} units; stopping after stage one costs {stage_costs[0]}")
    print(f"   the early negative result saves {total - stage_costs[0]} units\n")


def role_of_a_model() -> None:
    """Complete one sentence: the model predicts this quantity, for this object, measured by this assay, under these conditions."""
    heading(7, "The role of a model: one sentence that names object, quantity, assay and conditions")
    score, compound, assay = 0.91, "compound X", "assay A"
    print(f"   the model predicts an activity score of {score} for {compound} in {assay}")
    print("   it names the object, the measurement and the conditions, so later results can be compared fairly\n")


# ----------------------------------------------------------------------------------------------------- Part 2
def occupancy(concentration_nm: float, kd_nm: float) -> float:
    """Fraction of binding sites occupied: concentration / (concentration + KD)."""
    return concentration_nm / (concentration_nm + kd_nm)


def occupancy_examples() -> None:
    """A molecule with KD = 10 nM at four concentrations (nanomolar = one billionth of a mole per litre)."""
    heading(8, "Occupancy: fraction occupied = concentration / (concentration + KD), with KD = 10 nM")
    kd = 10
    for concentration in (1, 10, 100, 1000):
        print(f"   {concentration:5d} nM -> {occupancy(concentration, kd):6.1%}")
    print("   KD is the concentration at which half of the spaces are occupied; a smaller KD means tighter binding\n")


def affinity_and_potency() -> None:
    """The same molecule: half of the activity blocked at 10 nM in a test tube, at 1000 nM in a cell growth assay."""
    heading(9, "Affinity and potency: the number travels with its question")
    tube_nm, cells_micromolar = 10, 1.0
    cells_nm = cells_micromolar * 1000   # 1 micromolar = 1000 nanomolar
    print(f"   purified protein: {tube_nm} nM; cell growth: {cells_micromolar:g} uM = {cells_nm:g} nM")
    print(f"   a {cells_nm / tube_nm:.0f} fold shift, and both numbers are correct for their own assay\n")


def selectivity() -> None:
    """KD of 10 nM for the target, 50 nM for a close relative and 5000 nM for a distant relative."""
    heading(10, "Selectivity: ratios, and occupancy at one dose")
    kd = {"target": 10, "close relative": 50, "distant relative": 5000}
    for name in ("close relative", "distant relative"):
        print(f"   selectivity ratio for the {name}: {kd[name]} / {kd['target']} = {kd[name] / kd['target']:.0f} fold")
    dose = 100
    for name, value in kd.items():
        print(f"   at {dose} nM the {name} is {occupancy(dose, value):.1%} occupied")
    print("   same molecule, same dose, three different outcomes\n")


def exposure() -> None:
    """Peak 100 units at hour 1, half-life 4 hours, effect needs at least 30 units at the target."""
    heading(11, "Exposure: a bathtub that drains with a half-life")
    peak, peak_hour, half_life, needed = 100.0, 1, 4.0, 30.0
    for hour in (1, 5, 9, 13):
        level = peak * 0.5 ** ((hour - peak_hour) / half_life)
        print(f"   hour {hour:2d}: level {level:6.1f}")
    # solve peak * 0.5 ** ((t - 1) / half_life) = needed for t
    hour_below = peak_hour + half_life * math.log2(peak / needed)
    print(f"   the level falls below {needed:g} at hour {hour_below:.1f}: about {hour_below - peak_hour:.0f} hours of useful exposure")
    arriving_share = 0.10
    print(f"   if only {arriving_share:.0%} reaches the target, a target level of {needed:g} needs {needed / arriving_share:g} in the blood\n")


def evidence_ladder() -> None:
    """A docking score is a hypothesis; each experiment answers its own question."""
    heading(12, "The evidence ladder: which claim each number supports")
    rungs = [
        ("docking score -9.4", "hypothesis: this molecule may fit this pocket"),
        ("binding experiment, KD 20 nM", "the molecule binds the protein"),
        ("activity assay, half blocked at 40 nM", "the protein's function changes"),
        ("cell experiment, half the growth effect at 900 nM", "an effect in living cells"),
    ]
    for number, claim in rungs:
        print(f"   {number:52s} -> {claim}")
    print("   extra digits add precision: -9.43 looks more certain than -9, and the strength of evidence stays on its rung\n")


# ----------------------------------------------------------------------------------------------------- Part 3
def phosphate_counts() -> None:
    """ATP carries three phosphate groups, ADP two; the same for GTP and GDP."""
    heading(13, "Phosphate counts: the kinase switch and the KRAS battery")
    for before, after in (("ATP", "ADP"), ("GTP", "GDP")):
        print(f"   {before} has 3 phosphate groups, {after} has 2: the transfer releases {3 - 2} phosphate group")
    print("   EGFR (a kinase) attaches that phosphate to a protein; KRAS releases it, which is its off switch\n")


def reading_g12d(kras_start: str = "MTEYKLVVVGAG") -> None:
    """G12D: the old letter G, the position 12, the new letter D. Python counts from zero."""
    heading(14, "Reading the label G12D")
    old, position, new = "G", 12, "D"
    index = position - 1
    print(f"   first twelve letters: {', '.join(kras_start)}")
    print(f"   biological position {position} is Python index {index}, which holds {kras_start[index]!r} (expected {old!r})")
    print(f"   after the change the sequence begins: {', '.join(apply_mutation(kras_start, position, old, new))}\n")


def hash_examples() -> None:
    """A SHA-256 hash is a fingerprint of every byte; one changed letter gives an unrelated code."""
    heading(15, "Hashes: one letter apart, two unrelated fingerprints")
    for text in ("MTEYKLVVVGAG", "MTEYKLVVVGAD"):
        print(f"   {text}  sha256 = {hashlib.sha256(text.encode()).hexdigest()}")
    print("   the two codes differ from their very first characters\n")


def read_fasta(path: Path) -> str:
    """Return the sequence letters of a one-record FASTA file."""
    return "".join(line.strip() for line in path.read_text().splitlines() if not line.startswith(">"))


def isoforms() -> None:
    """KRAS isoform 4A (UniProt 2A, 189 letters) against isoform 4B (UniProt 2B, 188 letters)."""
    heading(16, "Isoforms: two editions of one book")
    record = json.loads((ROOT / "data/raw/uniprot-P01116.json").read_text())
    edition_a = record["sequence"]["value"]                          # 189 amino acids (the record used in Part 1)
    edition_b = read_fasta(ROOT / "data/raw/uniprot-P01116-2.fasta")  # 188 amino acids (the record used for the structure)
    first_difference = next(i + 1 for i, (a, b) in enumerate(zip(edition_a, edition_b)) if a != b)
    print(f"   isoform 4A: {len(edition_a)} amino acids; isoform 4B: {len(edition_b)} amino acids")
    print(f"   the first {first_difference - 1} positions are identical (position 12 holds {edition_a[11]} in both); they first differ at {first_difference}")
    print("   the manifest names the form explicitly: isoform 4B, accession P01116-2\n")


def structure_counts() -> None:
    """Deposited against modeled residues, resolution in angstroms, and the numbering shift for EGFR."""
    heading(17, "Structure counts: the group photograph")
    coordinates = json.loads((ROOT / "data/outputs/structure_coordinates.json").read_text())
    deposited = {"1M17": 333, "7RPZ": 170}
    for structure in coordinates["structures"]:
        pdb_id = structure["pdb_id"]
        modeled = len(structure["alpha_carbons"])
        entry = json.loads((ROOT / f"data/raw/rcsb-{pdb_id}-entry.json").read_text())
        resolution = entry["rcsb_entry_info"]["resolution_combined"][0]
        print(f"   {pdb_id}: deposited {deposited[pdb_id]}, modeled {modeled}, difference {deposited[pdb_id] - modeled}, resolution {resolution} angstrom")
    first = coordinates["structures"][0]["alpha_carbons"][0]
    print(f"   EGFR numbering: structure residue {first['author_position']} is UniProt residue {first['reference_position']}; "
          f"the difference of {first['reference_position'] - int(first['author_position'])} equals the 24-residue first segment")
    print("   a smaller resolution number means finer detail\n")


# ----------------------------------------------------------------------------------------------------- Part 4
def sequence_check() -> None:
    """The four checks of apply_mutation on the tiny example from its own description."""
    heading(18, "The sequence check: four checks before anything is returned")
    print(f"   apply_mutation('MAG', 2, 'A', 'D') -> {apply_mutation('MAG', 2, 'A', 'D')!r}")
    try:
        apply_mutation("MAG", 2, "G", "D")   # position 2 holds A, not G
    except ValueError as error:
        print(f"   expecting G at position 2 -> ValueError: {error}")
    print()


def coordinates() -> None:
    """The distance between the first two alpha carbons of 1M17, by hand and with math.dist."""
    heading(19, "Coordinates: neighbouring alpha carbons sit close to 3.8 angstrom apart")
    data = json.loads((ROOT / "data/outputs/structure_coordinates.json").read_text())
    carbons = data["structures"][0]["alpha_carbons"]
    first, second = carbons[0]["xyz"], carbons[1]["xyz"]
    differences = [abs(a - b) for a, b in zip(first, second)]
    squares = [d * d for d in differences]
    print(f"   {carbons[0]['residue']} at {first}, {carbons[1]['residue']} at {second}")
    print(f"   differences {[round(d, 3) for d in differences]}, squares {[round(s, 1) for s in squares]}, sum {sum(squares):.1f}")
    print(f"   distance = sqrt({sum(squares):.1f}) = {math.sqrt(sum(squares)):.2f} angstrom (math.dist gives {math.dist(first, second):.2f})")
    for structure in data["structures"]:
        spacing = [math.dist(structure["alpha_carbons"][i]["xyz"], structure["alpha_carbons"][i + 1]["xyz"]) for i in range(10)]
        print(f"   {structure['pdb_id']}: first ten pairs between {min(spacing):.2f} and {max(spacing):.2f} angstrom; "
              f"{len(structure['alpha_carbons'])} alpha carbons, {len(structure['selected_ligand_heavy_atoms'])} ligand heavy atoms")
    print()


def chemical_identity() -> None:
    """An InChIKey has 27 characters in three blocks; compare complete keys, never names."""
    heading(20, "Chemical identity: the InChIKey")
    from_structure = "SCLLZBIBSFTLIN-INOGPEIASA-N"        # the MRTX1133 ligand of structure 7RPZ
    name_search_record = "SCLLZBIBSFTLIN-IFMUVJFISA-N"    # the record that the name 'MRTX-1133' offered
    for label, key in (("ligand in the structure", from_structure), ("record found by name", name_search_record)):
        first, second, third = key.split("-")
        print(f"   {label}: {key}  ({len(key)} characters; blocks of {len(first)}, {len(second)} and {len(third)})")
    first_a, second_a, _ = from_structure.split("-")
    first_b, second_b, _ = name_search_record.split("-")
    print(f"   first blocks equal: {first_a == first_b} (same connections); second blocks equal: {second_a == second_b} (different arrangement in space)")
    candidates = json.loads((ROOT / "data/raw/chembl-mrtx1133-search.json").read_text())["molecules"]
    match = exact_compound(candidates, from_structure)
    print(f"   the name search returned {len(candidates)} records; the exact match is {match['molecule_chembl_id']}\n")


def rejecting_joins() -> None:
    """The four synthetic metadata comparisons of the compatibility audit, run with assess_join."""
    heading(21, "Rejecting a join: the conductor checks name, date and destination")
    reference = {"compound": "SCLLZBIBSFTLIN-INOGPEIASA-N", "target": "P01116-2", "endpoint": "biochemical inhibition",
                 "units": "nM", "variant": "G12D"}
    keys = tuple(reference)
    cases = [
        ("same declared metadata", dict(reference)),
        ("wrong variant", {**reference, "variant": "reference G12"}),
        ("different biological endpoint", {**reference, "endpoint": "cell viability"}),
        ("unknown variant", {**reference, "variant": None}),
    ]
    accepted = 0
    for label, other in cases:
        result = assess_join(reference, other, keys)
        accepted += result["compatible"]
        reasons = "; ".join(result["reasons"]) or "all five fields agree"
        print(f"   {label:30s} {'accepted' if result['compatible'] else 'rejected'}: {reasons}")
    print(f"   summary: {accepted} accepted, {len(cases) - accepted} rejected (these four records are synthetic metadata labels)\n")


def units_and_endpoints() -> None:
    """Converting units keeps the endpoint: 0.2 micromolar is 200 nanomolar, and a mean of two endpoints is a blend."""
    heading(22, "Units and endpoints")
    record_a_nm = 50          # inhibition of a purified protein, in nanomolar
    record_b_um = 0.2         # growth of cells after 72 hours, in micromolar
    record_b_nm = record_b_um * 1000
    print(f"   record A {record_a_nm} nM (protein activity); record B {record_b_um} uM = {record_b_nm:g} nM (cell growth)")
    print(f"   same unit now, different endpoints; their mean {(record_a_nm + record_b_nm) / 2:g} nM belongs to a blend of two experiments\n")


def missing_values() -> None:
    """Four compounds with activity values 12, 0, empty and 45."""
    heading(23, "Missing values: an empty cell is not a zero")
    values = [12, 0, None, 45]
    measured = [v for v in values if v is not None]
    zero_filled = [0 if v is None else v for v in values]
    print(f"   skipping the empty cell: mean = {sum(measured)} / {len(measured)} = {sum(measured) / len(measured):g}")
    print(f"   turning it into a zero:  mean = {sum(zero_filled)} / {len(zero_filled)} = {sum(zero_filled) / len(zero_filled):g}")
    print("   the second mean invents a measurement; the honest table keeps the empty cell with an explanation\n")


def main() -> None:
    """Run every worked example in the order of the video."""
    for example in (target_and_outcome, association, intervention, validation, screening_funnel, early_negative_result,
                    role_of_a_model, occupancy_examples, affinity_and_potency, selectivity, exposure, evidence_ladder,
                    phosphate_counts, reading_g12d, hash_examples, isoforms, structure_counts, sequence_check,
                    coordinates, chemical_identity, rejecting_joins, units_and_endpoints, missing_values):
        example()


if __name__ == "__main__":
    main()
