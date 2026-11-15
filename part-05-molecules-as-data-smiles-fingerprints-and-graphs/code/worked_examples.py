#!/usr/bin/env python3
"""worked_examples.py - the small calculations from Part 5 of the video, reproduced step by step.

What it does
    The video builds each hard idea from an everyday picture and a tiny example with numbers you can repeat by
    hand. This script runs the same examples in the same order, so you can check every number and then change
    the inputs. A small reader for a handful of SMILES symbols (about 60 lines) lets you watch a string turn into
    atoms, bonds, hydrogen counts, a formula and an adjacency matrix. The later examples read the real results
    saved in `data/outputs/` by `molecular_representation_lab.py`, so the standard library is all this file uses.

      Part 1 - recover the molecular graph
        1.  Towns and roads:       ethanol as 3 nodes and 2 edges, and why labels matter
        2.  Hydrogen counting:     each atom has a number of hands (valence); ethanol gives C2H6O
        3.  Same formula:          ethanol and dimethyl ether, mass 46.069, one donor against zero donors
        4.  Tables and matrices:   an atom table, a bond table and an adjacency matrix
        5.  Renumbering:           reversing the atom order and checking the mapping
        6.  Mirror images:         lactic acid, four different groups, two InChIKeys
      Part 2 - read and check molecular strings
        7.  Reading a string:      CCO, OCC and C(O)C recover the same graph
        8.  Rings:                 c1ccccc1 has six atoms and six bonds, the digit labels a bond between two atoms
        9.  Components:            the dot in sodium acetate and its two charges
        10. Parse and sanitize:    an unclosed ring against an oxygen with three bonds
        11. A toy canonical rule:  one winner among three spellings
        12. Stereo round trip:     the at signs, and what happens when they are dropped
      Part 3 - build and compare fingerprints
        13. Descriptors:           mass, donors and polar surface area
        14. Growing neighborhoods: the six environments of ethanol at radius 0 and 1
        15. Hashing and folding:   remainders after division, and a real collision at bit 1452
        16. Bits and counts:       dimethyl ether has 4 bits on and 6 occurrences
        17. Tanimoto:              the hand example, ethanol with ether, and the lactic acid pair
        18. MACCS keys:            nine positions on for ethanol, 167 stored positions for 166 keys
      Part 4 - the auditable lab
        19. The audit:             twenty inputs, five statuses
        20. A join:                one measurement attached to erlotinib through its InChIKey
        21. The exercises:         the three answers

What it needs
    Python 3.10 or newer and the standard library only. Examples 13 to 20 read the saved files in `data/outputs/`,
    so run the script from the folder that holds `code/` and `data/`. Every number is computed on your machine.

What to expect
    The numbers printed below match the video (rounded):
      ethanol C2H6O mass 46.069 and dimethyl ether C2H6O mass 46.069     donors 1 against 0
      benzene c1ccccc1: 6 atoms, 6 bonds, C6H6, mass 78.114             sodium acetate: charges -1 and +1
      lactic acid C3H6O3, mass 90.078, two InChIKeys ending REOHCLBHSA and UWTATZPHSA
      ethanol environments: 6 (radius 0 at 3 atoms, radius 1 at 3 atoms)  folded bits 807, 222, 80, 1057, 294, 1410
      17 mod 8 = 1 and 25 mod 8 = 1                                      1100037548 and 2115476908 both fold to bit 1452
      dimethyl ether: 4 bits on, 6 occurrences                           hand Tanimoto 2 / 4 = 0.5
      ethanol with dimethyl ether 1 / 9 = 0.11                           lactic acid pair 9 / 13 = 0.69 with chirality, 1.0 when chirality is left out
      acetic acid C2H4O2, mass 60.052                                   TPSA sums 20.23, 9.23, 37.30 and 57.53
      ethanol oxygen: 864662311 = 422198 x 2048 + 807                   acetic acid: 8 identifiers on 7 bits (bit 807)
      benzene: 18 environments, 3 identifiers, count 6 each             MACCS ethanol: 9 positions on of 167
      audit: 8 + 5 + 1 + 2 + 4 = 20                                     join: erlotinib key with 2.6 nM, activity 13852013

Run it:
    python code/worked_examples.py
"""
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "outputs"

# Average atomic weights (g/mol) used for the molar mass arithmetic.
WEIGHT = {"C": 12.011, "H": 1.008, "O": 15.999, "N": 14.007, "Na": 22.990}
# Valence = how many bonds an atom of this element normally makes (its "hands").
VALENCE = {"C": 4, "N": 3, "O": 2}


def heading(text):
    """Print a section heading so the output is easy to scan."""
    print()
    print("=" * 78)
    print(text)
    print("=" * 78)


# ---------------------------------------------------------------------------------------------
# A tiny SMILES reader. It understands: C N O (and aromatic c), = for a double bond, parentheses for
# branches, single-digit ring labels, [..] atoms with a charge or an H count, and the dot.
# It exists to make the idea visible, and it is far smaller than a real toolkit such as RDKit.
# ---------------------------------------------------------------------------------------------
def read_smiles(text):
    """Return (atoms, bonds). atoms: list of dicts; bonds: list of (i, j, order)."""
    atoms, bonds = [], []
    stack, ring_open = [], {}
    current, pending_order = None, 1
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            stack.append(current)            # remember where to come back to
        elif ch == ")":
            current = stack.pop()
        elif ch == ".":
            current, pending_order = None, 1  # a dot starts a new, disconnected component
        elif ch == "=":
            pending_order = 2
        elif ch.isdigit():
            if ch in ring_open:               # second time we see the digit: close the ring
                j = ring_open.pop(ch)
                aromatic = atoms[j]["aromatic"] and atoms[current]["aromatic"]
                bonds.append((j, current, 1.5 if aromatic else pending_order))
            else:                             # first time: remember this atom as one end of the ring
                ring_open[ch] = current
            pending_order = 1
        elif ch == "[":
            end = text.index("]", i)
            inside = text[i + 1:end]
            element = "Na" if inside.startswith("Na") else inside[0]
            charge = 1 if inside.endswith("+") else -1 if inside.endswith("-") else 0
            explicit_h = 1 if "H" in inside else 0
            atoms.append(dict(element=element, aromatic=False, charge=charge, explicit_h=explicit_h, bracket=True))
            current = _attach(atoms, bonds, current, pending_order); pending_order = 1
            i = end
        elif ch in "CNOcno":
            atoms.append(dict(element=ch.upper(), aromatic=ch.islower(), charge=0, explicit_h=0, bracket=False))
            current = _attach(atoms, bonds, current, pending_order); pending_order = 1
        i += 1
    return atoms, bonds


def _attach(atoms, bonds, previous, order):
    """Add the bond between the new atom and the atom before it (if any); return the new atom's index."""
    new = len(atoms) - 1
    if previous is not None:
        aromatic = atoms[previous]["aromatic"] and atoms[new]["aromatic"]
        bonds.append((previous, new, 1.5 if aromatic else order))
    return new


def hydrogens(atoms, bonds):
    """Hydrogen count per atom: valence minus the bonds drawn (bracket atoms state their own count)."""
    counts = []
    for index, atom in enumerate(atoms):
        if atom["bracket"]:
            counts.append(atom["explicit_h"]); continue
        used = sum(order for a, b, order in bonds if index in (a, b))
        counts.append(max(0, VALENCE[atom["element"]] - math.ceil(used)))
    return counts


def formula_and_mass(atoms, h_counts):
    """Hill-style formula (C first, then H, then the rest alphabetically) and average molar mass."""
    tally = {}
    for atom in atoms:
        tally[atom["element"]] = tally.get(atom["element"], 0) + 1
    tally["H"] = sum(h_counts)
    order = ["C", "H"] + sorted(k for k in tally if k not in ("C", "H"))
    text = "".join(k + (str(tally[k]) if tally[k] > 1 else "") for k in order if tally.get(k))
    mass = sum(WEIGHT[k] * n for k, n in tally.items())
    return text, mass


def adjacency(count, bonds):
    """Symmetric 0/1 adjacency matrix."""
    matrix = [[0] * count for _ in range(count)]
    for a, b, _ in bonds:
        matrix[a][b] = matrix[b][a] = 1
    return matrix


def same_graph(atoms_a, bonds_a, atoms_b, bonds_b):
    """True when some renumbering of graph B reproduces graph A (labels and bonds together)."""
    n = len(atoms_a)
    if n != len(atoms_b):
        return False
    edges_a = {(min(a, b), max(a, b)): order for a, b, order in bonds_a}
    for perm in itertools.permutations(range(n)):          # perm[i] = the index in B of atom i of A
        if any(atoms_a[i]["element"] != atoms_b[perm[i]]["element"] for i in range(n)):
            continue
        edges_b = {(min(perm[a], perm[b]), max(perm[a], perm[b])): order for (a, b), order in edges_a.items()}
        if edges_b == {(min(a, b), max(a, b)): order for a, b, order in bonds_b}:
            return True
    return False


def load(name):
    """Read a saved result file, or return None when the data folder is missing."""
    path = OUT / name
    return json.loads(path.read_text()) if path.exists() else None


# ---------------------------------------------------------------------------------------------
# Part 1 - recover the molecular graph
# ---------------------------------------------------------------------------------------------
def example_1_towns_and_roads():
    heading("1. Towns and roads: a molecule as a graph")
    atoms, bonds = read_smiles("CCO")
    print(f"ethanol CCO: {len(atoms)} heavy-atom nodes ({', '.join(a['element'] for a in atoms)}) and {len(bonds)} edges")
    for a, b, order in bonds:
        print(f"  edge {a}-{b}: {atoms[a]['element']} to {atoms[b]['element']}, bond order {order:g}")
    other, other_bonds = read_smiles("CCC")
    print(f"replace the oxygen by a carbon: {len(other)} nodes and {len(other_bonds)} edges, the same drawing, a different molecule")
    print("node labels and bond labels are part of the graph")


def example_2_hydrogen_counting():
    heading("2. Hydrogen counting: every atom has a number of hands")
    print("valence: carbon 4, nitrogen 3, oxygen 2, hydrogen 1")
    atoms, bonds = read_smiles("CCO")
    counts = hydrogens(atoms, bonds)
    for index, atom in enumerate(atoms):
        used = sum(order for a, b, order in bonds if index in (a, b))
        print(f"  atom {index} {atom['element']}: {used:g} bond(s) drawn, {VALENCE[atom['element']]} - {used:g} = {counts[index]} hydrogen(s)")
    text, mass = formula_and_mass(atoms, counts)
    print(f"total hydrogens {sum(counts)} -> formula {text}")
    print(f"mass = 2 x {WEIGHT['C']} + 6 x {WEIGHT['H']} + {WEIGHT['O']} = {2 * WEIGHT['C'] + 6 * WEIGHT['H'] + WEIGHT['O']:.3f} g/mol")


def example_3_same_formula():
    heading("3. The same formula can hide different connectivity")
    for name, smiles in (("ethanol", "CCO"), ("dimethyl ether", "COC")):
        atoms, bonds = read_smiles(smiles)
        counts = hydrogens(atoms, bonds)
        text, mass = formula_and_mass(atoms, counts)
        o_index = next(i for i, a in enumerate(atoms) if a["element"] == "O")
        donors = counts[o_index]
        print(f"  {name:<15} {smiles:<4} formula {text}, mass {mass:.3f}, hydrogens on oxygen (donors): {donors}")
    print("a donor count separates these two, while a formula or a mass column gives them the same value")


def example_4_tables_and_matrices():
    heading("4. An atom table, a bond table and an adjacency matrix (ethanol)")
    atoms, bonds = read_smiles("CCO")
    print("atom table :", [(i, a["element"]) for i, a in enumerate(atoms)])
    print("bond table :", [(a, b, "single") for a, b, _ in bonds])
    matrix = adjacency(len(atoms), bonds)
    print("adjacency matrix (row i, column j is 1 when atoms i and j are bonded):")
    for row in matrix:
        print("   ", row)
    print("symmetric:", all(matrix[i][j] == matrix[j][i] for i in range(3) for j in range(3)))
    print("bond types and atom labels travel beside the matrix")


def example_5_renumbering():
    heading("5. Renumbering the atoms gives the same molecule")
    forward, forward_bonds = read_smiles("CCO")
    backward, backward_bonds = read_smiles("OCC")
    print("forward  numbering:", [(i, a["element"]) for i, a in enumerate(forward)])
    print("backward numbering:", [(i, a["element"]) for i, a in enumerate(backward)])
    print("adjacency, forward :", adjacency(3, forward_bonds))
    print("adjacency, backward:", adjacency(3, backward_bonds))
    print("the matrices look identical, yet the labels moved: compare them only through a consistent mapping")
    print("same graph under some renumbering:", same_graph(forward, forward_bonds, backward, backward_bonds))
    ether, ether_bonds = read_smiles("COC")
    print("ethanol against dimethyl ether under any renumbering:", same_graph(forward, forward_bonds, ether, ether_bonds))


def example_6_mirror_images():
    heading("6. Lactic acid: two mirror arrangements")
    features = (OUT / "features.csv")
    print("the four different groups on the central carbon: CH3, OH, COOH and H")
    atoms, bonds = read_smiles("C[C@H](O)C(=O)O")
    counts = hydrogens(atoms, bonds)
    text, mass = formula_and_mass(atoms, counts)
    print(f"  formula {text}, mass {mass:.3f}  (the same for both mirror images)")
    if features.exists():
        rows = [line.split(",") for line in features.read_text().splitlines()]
        header = rows[0]
        for row in rows[1:]:
            if row[0] in ("lactic-at", "lactic-aat"):
                print(f"  {row[0]:<11} {row[header.index('canonical_isomeric_smiles')]:<20} InChIKey {row[header.index('standard_inchi_key')]}")
        print("the first block of the InChIKey agrees, and the stereo block differs: REOHCLBHSA against UWTATZPHSA")
    else:
        print("  (run from the part folder to read the saved features.csv with the two InChIKeys)")


# ---------------------------------------------------------------------------------------------
# Part 2 - read and check molecular strings
# ---------------------------------------------------------------------------------------------
def example_7_reading_a_string():
    heading("7. Reading a string: three spellings, one ethanol")
    reference = read_smiles("CCO")
    for text in ("CCO", "OCC", "C(O)C"):
        atoms, bonds = read_smiles(text)
        print(f"  {text:<6} atoms {''.join(a['element'] for a in atoms)}  bonds {[(a, b) for a, b, _ in bonds]}  "
              f"same graph as CCO: {same_graph(*reference, atoms, bonds)}")
    print("parentheses mark a branch and add zero atoms: they tell the reader where to return")
    # Acetic acid shows the alphabet at work: a branch, a double bond and the hands rule in one string.
    atoms, bonds = read_smiles("CC(=O)O")
    counts = hydrogens(atoms, bonds)
    text, mass = formula_and_mass(atoms, counts)
    print(f"  acetic acid CC(=O)O: {len(atoms)} atoms and {len(bonds)} bonds {[(a, b, order) for a, b, order in bonds]}")
    print(f"    hydrogens per atom {counts} -> {sum(counts)} hydrogens, formula {text}, mass {mass:.3f}")


def example_8_rings():
    heading("8. Rings: a digit joins two positions")
    atoms, bonds = read_smiles("c1ccccc1")
    counts = hydrogens(atoms, bonds)
    text, mass = formula_and_mass(atoms, counts)
    print(f"c1ccccc1: {len(atoms)} atoms and {len(bonds)} bonds (5 along the string + 1 closed by the digit)")
    print(f"  formula {text}, mass {mass:.3f}")
    kekule, kekule_bonds = read_smiles("C1=CC=CC=C1")
    kc = hydrogens(kekule, kekule_bonds)
    print(f"C1=CC=CC=C1 (Kekule): {len(kekule)} atoms, {len(kekule_bonds)} bonds, formula {formula_and_mass(kekule, kc)[0]}")
    print("two spellings, one benzene: the digit labels a connection between atoms that are already in the string")


def example_9_components():
    heading("9. Components: a dot keeps pieces apart")
    atoms, bonds = read_smiles("CC(=O)[O-].[Na+]")
    print(f"CC(=O)[O-].[Na+]: {len(atoms)} atoms, {len(bonds)} bonds")
    print("charges:", [(a["element"], a["charge"]) for a in atoms if a["charge"]], " sum =", sum(a["charge"] for a in atoms))
    seen, components = set(), 0
    neighbours = {i: set() for i in range(len(atoms))}
    for a, b, _ in bonds:
        neighbours[a].add(b); neighbours[b].add(a)
    for start in range(len(atoms)):
        if start in seen:
            continue
        components += 1
        todo = [start]
        while todo:
            node = todo.pop()
            if node not in seen:
                seen.add(node); todo.extend(neighbours[node])
    print(f"connected components: {components}  (the program records both pieces and sets the row aside under its single-component policy)")


def example_10_parse_and_sanitize():
    heading("10. Two checks: can it be read, and is the chemistry consistent?")
    for text, label in (("C1CC", "ring label 1 opens and stays open"), ("CO(C)C", "an oxygen with three single bonds")):
        atoms, bonds = read_smiles(text)
        open_rings = text.count("1") % 2 == 1
        problems = []
        if open_rings:
            problems.append("syntax: unclosed ring label")
        for index, atom in enumerate(atoms):
            used = sum(order for a, b, order in bonds if index in (a, b))
            if used > VALENCE[atom["element"]]:
                problems.append(f"chemistry: atom {index} ({atom['element']}) has {used:g} bonds, valence {VALENCE[atom['element']]}")
        print(f"  {text:<6} {label}: {problems or ['ok']}")
    print("an empty string and a missing value each become a visible rejected row, with the reason written beside it")


def example_11_toy_canonical():
    heading("11. A toy rule that picks one spelling")
    spellings = ["CCO", "OCC", "C(O)C"]
    winner = min(spellings, key=lambda s: (len(s), s))
    print("spellings:", spellings)
    print(f"toy rule: shortest spelling first, then alphabetical order -> {winner}")
    print("RDKit follows a more careful rule of its own and also writes CCO; the raw input stays beside it")


def example_12_stereo_round_trip():
    heading("12. Stereo notation survives only when it is kept")
    pair = ["C[C@H](O)C(=O)O", "C[C@@H](O)C(=O)O"]
    without = [text.replace("[C@@H]", "C").replace("[C@H]", "C") for text in pair]
    print("with at signs   :", pair, "-> two different strings")
    print("at signs removed:", without, "-> one string:", len(set(without)) == 1)
    print("removing the symbols loses information: two different molecules then share one text")


# ---------------------------------------------------------------------------------------------
# Part 3 - build and compare fingerprints
# ---------------------------------------------------------------------------------------------
def example_13_descriptors():
    heading("13. Descriptors: mass, donors and polar surface area")
    path = OUT / "features.csv"
    if not path.exists():
        print("  (run from the part folder to read the saved features.csv)"); return
    rows = [line.split(",") for line in path.read_text().splitlines()]
    header = rows[0]
    print(f"{'molecule':<16} {'MolWt':>8} {'TPSA':>7} {'donors':>7} {'acceptors':>10}")
    for row in rows[1:]:
        if row[0] in ("ethanol", "dimethyl-ether"):
            get = lambda name: row[header.index(name)]
            print(f"{row[0]:<16} {float(get('MolWt')):>8.3f} {float(get('TPSA')):>7.2f} {get('HBD'):>7} {get('HBA'):>10}")
    print("same formula, same mass, different donor count and surface area: columns capture different facts")
    # TPSA adds one fixed piece for every polar oxygen (or nitrogen). The pieces below are the ones RDKit applies to our molecules.
    piece = {"hydroxyl O (O-H)": 20.23, "ether O (C-O-C)": 9.23, "carbonyl O (C=O)": 17.07}
    recipe = {"ethanol": ["hydroxyl O (O-H)"], "dimethyl-ether": ["ether O (C-O-C)"],
              "acetic-acid": ["carbonyl O (C=O)", "hydroxyl O (O-H)"],
              "lactic-at": ["hydroxyl O (O-H)", "carbonyl O (C=O)", "hydroxyl O (O-H)"]}
    print("TPSA as a sum of fixed pieces, compared with the saved column:")
    for row in rows[1:]:
        if row[0] in recipe:
            total = round(sum(piece[name] for name in recipe[row[0]]), 2)
            print(f"  {row[0]:<15} {' + '.join(str(piece[name]) for name in recipe[row[0]])} = {total:>5.2f}   saved {float(row[header.index('TPSA')]):>5.2f}")


def example_14_growing_neighborhoods():
    heading("14. Growing neighborhoods: the environments of ethanol")
    data = load("fingerprints.json")
    if not data:
        print("  (run from the part folder to read the saved fingerprints.json)"); return
    environments = data["ethanol"]["morgan"]["environments"]
    print(f"{'center':>6} {'radius':>6} {'atoms':<10} {'sparse identifier':>18} {'folded bit':>11}")
    for env in sorted(environments, key=lambda e: (e["radius"], e["center_atom"])):
        print(f"{env['center_atom']:>6} {env['radius']:>6} {str(env['atom_indices']):<10} {env['sparse_identifier']:>18} {env['folded_bit']:>11}")
    by_radius = {r: sum(1 for e in environments if e["radius"] == r) for r in (0, 1, 2)}
    print("environments per radius:", by_radius, "(radius 2 repeats the radius-1 environment for a three-atom molecule)")
    # Folding by hand for the oxygen: divide by the vector length and keep the remainder.
    oxygen = next(e for e in environments if e["center_atom"] == 2 and e["radius"] == 0)["sparse_identifier"]
    quotient, remainder = divmod(oxygen, 2048)
    print(f"the oxygen: {oxygen} = {quotient} x 2048 + {remainder}, so it switches on bit {remainder}")


def example_15_hashing_and_folding():
    heading("15. Hashing and folding: remainders after division")
    for number in (17, 25):
        print(f"  {number} divided by 8 leaves remainder {number % 8}")
    print("different identifiers reach the same position of an 8-position vector")
    data = load("fingerprints.json")
    print("ethanol identifiers folded into 2048 positions:")
    if data:
        for env in sorted(data["ethanol"]["morgan"]["environments"], key=lambda e: e["folded_bit"]):
            print(f"  {env['sparse_identifier']:>11} mod 2048 = {env['sparse_identifier'] % 2048:>4}")
    for number in (1100037548, 2115476908):
        print(f"  erlotinib identifier {number} mod 2048 = {number % 2048}")
    print("two different identifiers, one occupied bit: a genuine folding collision at bit 1452")
    if data:
        erlotinib = data["erlotinib"]["morgan"]
        print(f"erlotinib: {len(erlotinib['sparse_counts'])} distinct identifiers, {erlotinib['num_on_bits']} occupied bits of 2048")
        # Acetic acid: group the identifiers by their remainder and report any bit that holds two different identifiers.
        acetic = [int(i) for i in data["acetic-acid"]["morgan"]["sparse_counts"]]
        bins = {}
        for identifier in acetic:
            bins.setdefault(identifier % 2048, []).append(identifier)
        print(f"acetic acid: {len(acetic)} identifiers fold into {len(bins)} bits")
        for bit, identifiers in sorted(bins.items()):
            if len(identifiers) > 1:
                print(f"  collision at bit {bit}: identifiers {identifiers}")


def example_16_bits_and_counts():
    heading("16. Presence and frequency")
    data = load("fingerprints.json")
    if not data:
        print("  (run from the part folder to read the saved fingerprints.json)"); return
    for name in ("ethanol", "dimethyl-ether"):
        counts = data[name]["morgan"]["count_vector"]
        print(f"  {name:<15} bits on {len(counts)}, total occurrences {sum(counts.values())}, counts {dict(counts)}")
    print("dimethyl ether has two identical methyl groups: bit 1057 and bit 841 each count 2, bits record presence and counts record how often")
    benzene = data["benzene"]["morgan"]
    print(f"  benzene: {len(benzene['environments'])} environments (6 atoms x radius 0, 1 and 2) share {len(benzene['sparse_counts'])} identifiers")
    print(f"           sparse counts {benzene['sparse_counts']}, bits on {benzene['on_bits']}")
    print("six identical carbons repeat every environment six times: the count vector shows it and the bit vector does not")


def tanimoto(a, b):
    """Shared on-bits divided by on-bits in either fingerprint."""
    return len(a & b) / len(a | b)


def example_17_tanimoto():
    heading("17. Tanimoto: shared over total")
    a, b = {1, 3, 5}, {1, 5, 7}
    print(f"hand example A {sorted(a)}, B {sorted(b)}: shared {sorted(a & b)}, union {sorted(a | b)}")
    print(f"  {len(a & b)} / {len(a | b)} = {tanimoto(a, b)}")
    print(f"  same with counts: ({len(a)} + {len(b)} - {len(a & b)}) = {len(a) + len(b) - len(a & b)} in the union")
    data = load("fingerprints.json")
    if not data:
        print("  (run from the part folder to read the saved fingerprints.json)"); return
    bits = lambda name: {int(k) for k in data[name]["morgan"]["count_vector"]}
    ethanol, ether = bits("ethanol"), bits("dimethyl-ether")
    print(f"ethanol with dimethyl ether: shared {sorted(ethanol & ether)}, union {len(ethanol | ether)} -> {len(ethanol & ether)} / {len(ethanol | ether)} = {tanimoto(ethanol, ether):.3f}")
    lactic_a, lactic_b = bits("lactic-at"), bits("lactic-aat")
    print(f"lactic acid pair, chirality included: {len(lactic_a & lactic_b)} / {len(lactic_a | lactic_b)} = {tanimoto(lactic_a, lactic_b):.3f}")
    print(f"  each partner has {len(lactic_a)} bits on; shared {len(lactic_a & lactic_b)}; only in A {sorted(lactic_a - lactic_b)}; only in B {sorted(lactic_b - lactic_a)}")
    print(f"  union = {len(lactic_a & lactic_b)} + {len(lactic_a - lactic_b)} + {len(lactic_b - lactic_a)} = {len(lactic_a | lactic_b)}, and also {len(lactic_a)} + {len(lactic_b)} - {len(lactic_a & lactic_b)} = {len(lactic_a) + len(lactic_b) - len(lactic_a & lactic_b)}")
    payload = load("lesson_payload.json")
    if payload:
        print(f"lactic acid pair, chirality left out (saved result): {payload['stereo_comparison']['achiral_tanimoto']}")
    print("these numbers describe the overlap of two encodings, which is a separate question from potency")


def example_18_maccs():
    heading("18. MACCS keys: a fixed questionnaire")
    data = load("fingerprints.json")
    if not data:
        print("  (run from the part folder to read the saved fingerprints.json)"); return
    maccs = data["ethanol"]["maccs"]
    print(f"RDKit stores {maccs['storage_bits']} positions for {maccs['public_key_numbers']} keys (position 0 is a placeholder)")
    print(f"ethanol: {len(maccs['on_bits'])} positions on: {maccs['on_bits']}")
    print("every molecule gets the same 167 positions, so each position asks the same question across molecules")


# ---------------------------------------------------------------------------------------------
# Part 4 - the auditable lab
# ---------------------------------------------------------------------------------------------
def example_19_the_audit():
    heading("19. The audit: twenty rows, five statuses")
    payload = load("lesson_payload.json")
    if not payload:
        print("  (run from the part folder to read the saved lesson_payload.json)"); return
    counts = payload["matrix_status_counts"]
    for status, number in counts.items():
        print(f"  {status:<30} {number}")
    print(" + ".join(str(v) for v in counts.values()), "=", sum(counts.values()))
    print("every category keeps its reason: a salt, an alias and unreadable text each mean something different")


def example_20_a_join():
    heading("20. A join: attach one measurement to one molecule through the compound key")
    payload, features = load("lesson_payload.json"), OUT / "features.csv"
    if not payload or not features.exists():
        print("  (run from the part folder to read the saved results)"); return
    rows = [line.split(",") for line in features.read_text().splitlines()]
    header = rows[0]
    structure = next(dict(zip(header, row)) for row in rows[1:] if row[0] == "erlotinib")
    measurement = payload["prerequisites"]["separate_measured_record"]
    print("table 1 (structure):  key", structure["standard_inchi_key"], " canonical", structure["canonical_isomeric_smiles"])
    print("table 2 (measurement):", {k: measurement[k] for k in ("standard_inchi_key", "standard_value", "standard_units", "standard_type", "activity_id", "assay_chembl_id") if k in measurement})
    if structure["standard_inchi_key"] == measurement["standard_inchi_key"]:
        print("the full keys match, so the join attaches this measurement to this molecule; the feature table itself keeps structure columns only")


def example_21_the_exercises():
    heading("21. The three exercises")
    reference = read_smiles("CCO")
    for text in ("CCO", "OCC", "C(O)C"):
        atoms, bonds = read_smiles(text)
        print(f"  exercise 1: {text:<6} is the ethanol graph: {same_graph(*reference, atoms, bonds)}")
    ether = read_smiles("COC")
    print(f"              ethanol against dimethyl ether (same formula): {same_graph(*reference, *ether)}")
    print(f"  exercise 2: hand Tanimoto {len({1, 3, 5} & {1, 5, 7})} / {len({1, 3, 5} | {1, 5, 7})} = 0.5, against 1 / 9 = {1 / 9:.3f} for ethanol with dimethyl ether")
    print("  exercise 3: an alias, the salt and the incomplete stereo record each get their own status, and the reason travels with the row")


def main():
    for example in (example_1_towns_and_roads, example_2_hydrogen_counting, example_3_same_formula,
                    example_4_tables_and_matrices, example_5_renumbering, example_6_mirror_images,
                    example_7_reading_a_string, example_8_rings, example_9_components,
                    example_10_parse_and_sanitize, example_11_toy_canonical, example_12_stereo_round_trip,
                    example_13_descriptors, example_14_growing_neighborhoods, example_15_hashing_and_folding,
                    example_16_bits_and_counts, example_17_tanimoto, example_18_maccs, example_19_the_audit,
                    example_20_a_join, example_21_the_exercises):
        example()
    print()
    print("Done. Change a SMILES string or a bit set at the top of an example and run it again.")


if __name__ == "__main__":
    main()
