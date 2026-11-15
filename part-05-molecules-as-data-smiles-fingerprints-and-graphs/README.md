# Part 5: Molecules as data, SMILES, fingerprints and graphs

Code for the fifth video of the course. The video follows one question: how does a molecule written as a text string become checked, named numbers that a model could use? The lab reads 20 deliberately chosen input rows, recovers each molecule's graph, builds identities, descriptors and fingerprints, compares fingerprints, and keeps every decision visible. It is a representation pipeline: it prepares checked, named numbers, and the lessons that follow use such numbers to train models and to study activity.

The video explains what the code does and why, starting from everyday pictures (towns and roads, a spelling that reads left to right, neighborhoods that grow, a coat-check with numbered hooks) and tiny worked numbers. The line-by-line reading lives in the commented files in this folder, and the Medium article walks through the same steps in writing.

## What is in this folder

| Path | What it is |
|------|------------|
| `code/molecular_representation_lab.py` | The lab. Every step has a comment that explains what it does and why. |
| `code/worked_examples.py` | The small calculations from the video, step by step: ethanol as three nodes and two edges, hydrogen counting by valence, the same formula with different connectivity, an atom table, a bond table and an adjacency matrix, renumbering, the two mirror images of lactic acid, three spellings of ethanol, acetic acid read with the SMILES alphabet, the ring digit of benzene, the dot of sodium acetate, the parse check and the sanitize check, a toy rule that picks one spelling, the stereo round trip, descriptors with polar surface area added up piece by piece, the six Morgan environments of ethanol, folding by remainder, the collisions of acetic acid and erlotinib, bits against counts with benzene's symmetry, Tanimoto by hand and for the lactic acid pair, MACCS keys, the audit total of 20, a join of one measurement to erlotinib and the three exercises. Standard library only; the later sections read the saved results in `data/outputs/`. |
| `code/test_molecular_representation_lab.py` | Twenty-two checks, one scientific claim each, run with RDKit and offline. |
| `code/requirements.txt` | The package versions used for the saved results (RDKit, NumPy, Pillow). |
| `data/raw/representation_inputs.json` | The 20 input rows: equivalent spellings, different molecules, a salt, unspecified stereochemistry and broken strings. |
| `data/raw/INPUT_LOCK.json` | The SHA-256 hash of all 20 saved input files; the lab checks it before it starts. |
| `data/raw/current/`, `data/raw/prerequisites/` | The saved ChEMBL and RCSB records, and the results of Parts 3 and 4 that this lab builds on. |
| `data/outputs/` | The results of the run shown in the video: the lesson payload, features, fingerprints, graphs, audits, bit tables and a run receipt. |

The lab also draws a 2D picture of each accepted molecule when you run it. Those pictures are written to `data/outputs/depictions/` on your machine and stay out of this repository to keep it small.

## What the script does

1. Checks that its saved inputs are unchanged and that the results of Parts 3 and 4 are the ones it expects.
2. Parses every string with RDKit, sanitizes it and records why any row fails. Every row stays visible with its reason.
3. For each readable molecule, records an identity (canonical SMILES and a standard InChIKey) and seven descriptors.
4. Gives each row a status: accepted, alias, excluded multi-component, excluded unspecified stereochemistry, retained comparison or rejected.
5. Exports each molecule as a labeled graph: atoms, bonds, adjacency matrix and 2D drawing coordinates.
6. Builds a Morgan fingerprint (radius 2, 2048 bits) and a MACCS fingerprint, keeping sparse counts, folded counts and bits separate, and shows a real folding collision.
7. Compares fingerprints with the Tanimoto coefficient.
8. Writes the JSON and CSV files, the pictures and a run receipt.

## What you should see

| Quantity | Value |
|----------|-------|
| Input rows | 20: 8 accepted, 5 aliases, 1 salt kept whole, 2 with unspecified stereochemistry, 4 rejected |
| Ethanol and dimethyl ether | same formula C2H6O and mass 46.069 g/mol; Morgan Tanimoto 1/9, about 0.11 |
| Two lactic acid mirror images | different InChIKeys; chiral Morgan similarity 9/13, about 0.69; with chirality off, 1.0 |
| Erlotinib | 48 distinct sparse identifiers, 47 set bits of 2048: identifiers 1100037548 and 2115476908 both fold to bit 1452 |
| Tiny 8-bit example | collisions throughout |
| Hand example, sets {1,3,5} and {1,5,7} | 2 shared / 4 in the union = 0.5 |

These numbers compare representations, so they describe the overlap of two encodings and answer a different question from potency. A similarity of 1 can still hide a stereochemistry difference when the representation leaves stereochemistry out, as the lactic acid pair shows.

## How to run it

You need Python 3.10 or newer. The lab and its tests need the packages in `code/requirements.txt` (`pip install -r code/requirements.txt`) and run fully offline with the saved inputs. `worked_examples.py` needs the standard library only.

```
python code/worked_examples.py
python code/molecular_representation_lab.py
python -m unittest discover -s code -p "test_molecular_representation_lab.py" -v
```

`worked_examples.py` prints each calculation under a numbered heading in video order. Expect these numbers: ethanol C2H6O with mass 46.069 and dimethyl ether with the same formula and mass (1 donor against 0); benzene c1ccccc1 with 6 atoms, 6 bonds, C6H6 and mass 78.114; sodium acetate with charges -1 and +1; lactic acid C3H6O3 with mass 90.078 and two InChIKeys; ethanol's six environments with folded bits 807, 222, 80, 1057, 294 and 1410; acetic acid C2H4O2 with mass 60.052; polar surface area sums 20.23, 9.23, 37.30 and 57.53; the oxygen of ethanol as 422198 x 2048 + 807; acetic acid with 8 identifiers on 7 bits; benzene with 18 environments and 3 identifiers counted 6 times each; dimethyl ether with 4 bits and 6 occurrences; the hand Tanimoto 2 / 4 = 0.5, ethanol with dimethyl ether 1 / 9 and the lactic acid pair 9 / 13 against 1.0 when chirality is left out; MACCS with 9 positions on for ethanol; the audit total 8 + 5 + 1 + 2 + 4 = 20; and the erlotinib join with its 2.6 nM record.

Add `--root PATH` to the first command to use another copy of the data folder. The saved results were made with Python 3.12, RDKit 2026.09.2, NumPy 2.5.4 and Pillow 13.0.0. With other RDKit versions, some fingerprint bit numbers or calculated descriptors can differ in the last digits.

## How the inputs and policies work

- The eight main rows are ethanol, dimethyl ether, benzene, two specified lactic acid stereoisomers, acetic acid, erlotinib (CHEMBL553, ligand AQ4) and the exact MRTX1133 ligand (CHEMBL5081048, ligand 6IC).
- Five aliases stay visible: two ethanol spellings, benzene's Kekule form, and the structure-file spellings of the two recurring compounds.
- Sodium acetate stays an intact two-component salt (charges -1 and +1), with both fragments kept exactly as written.
- Unspecified lactic acid stereochemistry and the partly specified MRTX-1133 name record stay outside the main matrix, as explicit comparisons.
- Missing, empty, unclosed-ring and invalid-valence inputs each have an explicit rejected row with its reason, and every failure stays visible as a failure.
- Canonical SMILES come from this RDKit version and give each molecule one reproducible spelling; tautomer, protonation and salt standardization are separate topics for later. Standard InChIKeys are checked against the complete keys from the sources, and every identity join uses a full key or identifier.

## What is calculated

`features.csv` has seven named numeric columns: average molecular mass, calculated Wildman-Crippen logP, topological polar surface area (nitrogen and oxygen contributions only), hydrogen-bond donors and acceptors, heavy-atom count and rotatable bonds. Calculated logP is a calculated estimate that sits beside measured solubility as a separate quantity.

Morgan settings are explicit: radius 2, 2048 bits, chirality on, bond types on, count simulation off. `fingerprints.json` keeps presence bits, folded counts, sparse hashed identifiers with their counts, and the atoms and bonds of every environment. MACCS uses RDKit's 166 public keys in 167 storage positions (position 0 is unused). It is a different representation that answers the question with fixed, named keys, where Morgan hashes whatever neighborhoods it finds.

`graphs.json` keeps atom labels, charges, hydrogen counts, aromatic and stereo attributes, bond types, components and the adjacency matrix. The 2D coordinates are a calculated drawing, and 3D coordinates and binding poses belong to later lessons.

The Part 4 result (IC50 of 2.6 nM, activity 13852013, assay CHEMBL3095060) is carried along as context and stays in its own record, apart from the feature rows, which hold structure information only.

## About the comments

The scripts were annotated for this tutorial. The comments and docstrings were added while every working line stayed as it was: the parsed syntax tree of each annotated file is identical to the original, apart from docstrings (SHA-256 of the file that produced the saved results, `molecular_representation_lab.py`: `b7ad533db987df5fe61347ea1037aa6928fe6c5427f1e6d9dbd4e66df5cfc8e2`, which is the `code_sha256` value in the saved `run_receipt.json`). The check performed on the annotated files is the syntax-tree comparison, and the full re-run of the lab and its tests happens on your machine with RDKit installed. The saved input hashes were verified (all 20 match `INPUT_LOCK.json`). If a test reports a difference on your machine, check your RDKit version first. The `command` text inside the saved receipt shows the path used when the video was recorded; in this repository run `python code/molecular_representation_lab.py`.

Data licences: ChEMBL is CC BY-SA 3.0 (credit ChEMBL/EMBL-EBI), PDB archive data is CC0, RDKit is BSD 3-clause.
