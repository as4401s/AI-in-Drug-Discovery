# Part 5: Molecules as data, SMILES, fingerprints and graphs

Code for the fifth video of the course. The video follows one question: how does a molecule written as a text string become checked, named numbers that a model could use? The lab reads 20 deliberately chosen input rows, recovers each molecule's graph, builds identities, descriptors and fingerprints, compares fingerprints, and keeps every decision visible. It is not a trained model, it generates no new drug, and it predicts nothing about activity.

## What is in this folder

| Path | What it is |
|------|------------|
| `code/molecular_representation_lab.py` | The lab. Every step has a comment that explains what it does and why. |
| `code/test_molecular_representation_lab.py` | Twenty-two checks, one scientific claim each, run with RDKit and offline. |
| `code/requirements.txt` | The package versions used for the saved results (RDKit, NumPy, Pillow). |
| `data/raw/representation_inputs.json` | The 20 input rows: equivalent spellings, different molecules, a salt, unspecified stereochemistry and broken strings. |
| `data/raw/INPUT_LOCK.json` | The SHA-256 hash of all 20 saved input files; the lab checks it before it starts. |
| `data/raw/current/`, `data/raw/prerequisites/` | The saved ChEMBL and RCSB records, and the results of Parts 3 and 4 that this lab builds on. |
| `data/outputs/` | The results of the run shown in the video: the lesson payload, features, fingerprints, graphs, audits, bit tables and a run receipt. |

The lab also draws a 2D picture of each accepted molecule when you run it. Those pictures are written to `data/outputs/depictions/` and are not stored in this repository.

## What the script does

1. Checks that its saved inputs are unchanged and that the results of Parts 3 and 4 are the ones it expects.
2. Parses every string with RDKit, sanitizes it and records why any row fails. Nothing is silently dropped.
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

These are comparisons of representations, never potency percentages. A similarity of 1 does not guarantee identical stereochemistry if the representation leaves it out.

## How to run it

You need Python 3.10 or newer and the packages in `code/requirements.txt` (`pip install -r code/requirements.txt`). No network, account or model file is used.

```
python code/molecular_representation_lab.py
python -m unittest discover -s code -p "test_molecular_representation_lab.py" -v
```

Add `--root PATH` to the first command to use another copy of the data folder. The saved results were made with Python 3.12, RDKit 2026.09.2, NumPy 2.5.4 and Pillow 13.0.0. With other RDKit versions, some fingerprint bit numbers or calculated descriptors can differ in the last digits.

## How the inputs and policies work

- The eight main rows are ethanol, dimethyl ether, benzene, two specified lactic acid stereoisomers, acetic acid, erlotinib (CHEMBL553, ligand AQ4) and the exact MRTX1133 ligand (CHEMBL5081048, ligand 6IC).
- Five aliases stay visible: two ethanol spellings, benzene's Kekule form, and the structure-file spellings of the two recurring compounds.
- Sodium acetate stays an intact two-component salt (charges -1 and +1). No fragment is selected, neutralized or replaced.
- Unspecified lactic acid stereochemistry and the partly specified MRTX-1133 name record stay outside the main matrix, as explicit comparisons.
- Missing, empty, unclosed-ring and invalid-valence inputs have explicit rejected rows. A failure never becomes zero-valued features.
- Canonical SMILES come from this RDKit version. This is not tautomer, protonation or salt standardization. Standard InChIKeys are checked against the complete keys from the sources, and no identity join uses a name alone.

## What is calculated

`features.csv` has seven named numeric columns: average molecular mass, calculated Wildman-Crippen logP, topological polar surface area (without sulfur and phosphorus), hydrogen-bond donors and acceptors, heavy-atom count and rotatable bonds. Calculated logP is not measured solubility.

Morgan settings are explicit: radius 2, 2048 bits, chirality on, bond types on, count simulation off. `fingerprints.json` keeps presence bits, folded counts, sparse hashed identifiers with their counts, and the atoms and bonds of every environment. MACCS uses RDKit's 166 public keys in 167 storage positions (position 0 is unused). It is a different representation, not a shorter copy of Morgan.

`graphs.json` keeps atom labels, charges, hydrogen counts, aromatic and stereo attributes, bond types, components and the adjacency matrix. The 2D coordinates are a calculated drawing, not measured 3D coordinates or binding poses.

The Part 4 result (IC50 of 2.6 nM, activity 13852013, assay CHEMBL3095060) is carried along only as context. No potency field is added to the feature rows and nothing is pooled.

## About the comments

The scripts were annotated for this tutorial. The comments and docstrings were added without changing any working line: the parsed syntax tree of each annotated file is identical to the original, apart from docstrings (SHA-256 of the file that produced the saved results, `molecular_representation_lab.py`: `b7ad533db987df5fe61347ea1037aa6928fe6c5427f1e6d9dbd4e66df5cfc8e2`, which is the `code_sha256` value in the saved `run_receipt.json`). RDKit could not be installed in the environment where the annotation was done, so the annotated lab and its tests were **not re-run** there; the check is the syntax-tree comparison. The saved input hashes were verified (all 20 match `INPUT_LOCK.json`). If a test fails on your machine, please check your RDKit version first. The `command` text inside the saved receipt shows the path used when the video was recorded; in this repository run `python code/molecular_representation_lab.py`.

Data licences: ChEMBL is CC BY-SA 3.0 (credit ChEMBL/EMBL-EBI), PDB archive data is CC0, RDKit is BSD 3-clause.
