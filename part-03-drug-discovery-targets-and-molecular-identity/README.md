# Part 3: Drug discovery targets and molecular identity

Code for the third video of the course. The video asks a question that comes before any model: are the protein, the structure and the compound we name exactly the ones we think they are? The code builds a small, checked "manifest" for two teaching targets, EGFR with erlotinib and KRAS G12D with MRTX1133, from frozen public records. It is an identity foundation: docking, dose-response curves, potency prediction and target validation come in later lessons.

The video explains what the code does and why. The line-by-line reading lives in the commented files in this folder, and the Medium article walks through the same steps in writing.

## What is in this folder

| Path | What it is |
|------|------------|
| `code/target_manifest_demo.py` | The main script. It verifies the saved records, checks every identity and builds the manifest. Every step has a comment that explains what it does and why. |
| `code/fetch_sources.py` | Downloads the 16 public source files (only needed to refresh them; they are already in `data/raw/`). |
| `code/worked_examples.py` | The small calculations from the video, step by step: growth with and without a blocking molecule, the funnel from 10,000 molecules to 32 hits, occupancy and KD, selectivity ratios, a half-life and exposure, the evidence ladder, reading G12D (position 12 is index 11), two SHA-256 hashes, isoform 4A against 4B, deposited against modeled residues, the distance between neighbouring alpha carbons, the InChIKey blocks, the four metadata checks, a unit conversion and missing values. Standard library only. |
| `code/test_target_manifest_demo.py` | Eight offline checks, one per safeguard of the main script. |
| `data/raw/` | The 16 saved source records: UniProt (EGFR P00533, KRAS P01116 and isoform 2B), RCSB PDB entries and coordinate files for 1M17 and 7RPZ, the ligand records AQ4 and 6IC, and ChEMBL records. |
| `research/download_receipts.json` | For every saved file: where it came from, when, its size and its SHA-256 hash. |
| `data/outputs/` | The results of the run shown in the video: the manifest, a compatibility audit, structure coordinates, a summary and a run receipt. |

## What the video covers

1. Part 1, from observation to a target: target and outcome, association, intervention, validation, the pipeline from hit to lead, and the roles of models. Each idea starts with an everyday picture and a worked example with small numbers.
2. Part 2, can a molecule change it?: binding and occupancy, affinity and potency, selectivity, druggability, exposure, modalities and the evidence ladder.
3. Part 3, our two targets: EGFR as a kinase receptor with erlotinib, KRAS and the label G12D, sequences, accessions and hashes, isoforms, and what a structure entry holds.
4. Part 4, connect the evidence: the eight steps of the program, the checks on sequence, structure and compound identity, rejecting mismatched records, units, endpoints and missing values.

Overview-only items return later: dose-response curves and IC50 in Part 4 of the course, the prediction models in Parts 6 and 7, and absorption, distribution, metabolism, excretion and toxicity in Parts 11 and 12.

## What the script does

1. Re-checks the size and hash of all 16 saved source files.
2. Confirms each protein record (accession, gene, human, sequence length).
3. Builds the KRAS G12D sequence from the natural isoform 2B with a checked one-based substitution.
4. Reads the structure files, maps each residue to its UniProt position and lists the differences between the crystal construct and the reference sequence.
5. Extracts the alpha-carbon and ligand coordinates that are really stored in the structure files.
6. Matches each ligand to ChEMBL by its complete InChIKey, not by name.
7. Runs four synthetic metadata checks that show when two assay records must not be joined.
8. Writes the manifest, audit, coordinates, summary and run receipt.

## What you should see

| Quantity | Value |
|----------|-------|
| Targets, reference compounds, source snapshots | 2, 2 and 16 |
| EGFR reference sequence | 1210 residues |
| Structure 1M17 (EGFR with erlotinib) | 333 deposited residues, 312 modeled |
| KRAS isoform 2B reference | 188 residues (Part 1 used the 189-residue isoform 2A) |
| Structure 7RPZ (KRAS with MRTX1133) | 170 deposited, 168 modeled; differs from the reference at G12D, C51S, C80L, C118S |
| MRTX1133 name search | 8 records; the exact ligand match is CHEMBL5081048 |
| Synthetic metadata joins | 1 accepted, 3 rejected |
| Bioactivity records | 0 (they come in Part 4) |

A crystal structure is a model of one construct under one set of conditions. A matching identifier is evidence that two records describe the same thing, not proof that two experiments are comparable.

## How to run the worked examples

```
python code/worked_examples.py
```

It prints every small calculation from the video with its numbers: growth 800 and 300 (a drop of 62.5 %), the funnel 10,000, 120, 70, 35 and 32, occupancy of 9.1 %, 50 %, 90.9 % and 99.0 % at KD = 10 nM, selectivity of 5 fold and 500 fold, about 7 hours of useful exposure, MTEYKLVVVGAG becoming MTEYKLVVVGAD with two unrelated SHA-256 codes, KRAS isoforms that first differ at position 151, 333 against 312 and 170 against 168 residues, an alpha-carbon distance of 3.81 angstrom, InChIKey blocks of 14, 10 and 1 characters, 1 accepted and 3 rejected metadata joins, 0.2 micromolar as 200 nanomolar, and means of 19 against 14.25.

## How to run the program

You need Python 3.10 or newer. Nothing else: the scripts use only the standard library and no network.

```
python code/target_manifest_demo.py
python -m unittest discover -s code -p "test_target_manifest_demo.py" -v
```

The script writes its results to `data/outputs/` (or to another folder with `--output-dir`). Running `python code/fetch_sources.py` prints "Preserved ..." for every file, because they are already saved. To download fresh copies, move `data/raw/` and `research/download_receipts.json` aside first; the databases change over time, so fresh copies can differ from the ones in the video.

## About the comments

The scripts were annotated for this tutorial. The comments and docstrings were added without changing any working line: the parsed syntax tree of each annotated file is identical to the file that produced the saved results (SHA-256 of that file, `target_manifest_demo.py`: `27949daa701e1738c501b2eba517a3aaf8bcc88a5e1f938407e0489c90efd505`). To check the annotated code, all eight tests were run and the script was run again on the saved data: the manifest, audit, coordinates and summary files were identical to the saved results, byte for byte. Only `run_receipt.json` changes between runs, because it records the time and the code hash. The `command` text inside the saved receipt shows the path that was used when the video was recorded; in this repository the command is `python code/target_manifest_demo.py`.

Data licences: UniProt is CC BY 4.0, PDB archive data is CC0, ChEMBL is CC BY-SA 3.0 (credit ChEMBL/EMBL-EBI).
