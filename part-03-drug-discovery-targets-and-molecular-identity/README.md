# Part 3: Drug discovery targets and molecular identity

Code for the third video of the course. The video asks a question that comes before any model: are the protein, the structure and the compound we name exactly the ones we think they are? The code builds a small, checked "manifest" for two teaching targets, EGFR with erlotinib and KRAS G12D with MRTX1133, from frozen public records. It does no docking, no potency prediction and no target validation.

## What is in this folder

| Path | What it is |
|------|------------|
| `code/target_manifest_demo.py` | The main script. It verifies the saved records, checks every identity and builds the manifest. Every step has a comment that explains what it does and why. |
| `code/fetch_sources.py` | Downloads the 16 public source files (only needed to refresh them; they are already in `data/raw/`). |
| `code/test_target_manifest_demo.py` | Eight offline checks, one per safeguard of the main script. |
| `data/raw/` | The 16 saved source records: UniProt (EGFR P00533, KRAS P01116 and isoform 2B), RCSB PDB entries and coordinate files for 1M17 and 7RPZ, the ligand records AQ4 and 6IC, and ChEMBL records. |
| `research/download_receipts.json` | For every saved file: where it came from, when, its size and its SHA-256 hash. |
| `data/outputs/` | The results of the run shown in the video: the manifest, a compatibility audit, structure coordinates, a summary and a run receipt. |

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

## How to run it

You need Python 3.10 or newer. Nothing else: the scripts use only the standard library and no network.

```
python code/target_manifest_demo.py
python -m unittest discover -s code -p "test_target_manifest_demo.py" -v
```

The script writes its results to `data/outputs/` (or to another folder with `--output-dir`). Running `python code/fetch_sources.py` prints "Preserved ..." for every file, because they are already saved. To download fresh copies, move `data/raw/` and `research/download_receipts.json` aside first; the databases change over time, so fresh copies can differ from the ones in the video.

## About the comments

The scripts were annotated for this tutorial. The comments and docstrings were added without changing any working line: the parsed syntax tree of each annotated file is identical to the file that produced the saved results (SHA-256 of that file, `target_manifest_demo.py`: `27949daa701e1738c501b2eba517a3aaf8bcc88a5e1f938407e0489c90efd505`). To check the annotated code, all eight tests were run and the script was run again on the saved data: the manifest, audit, coordinates and summary files were identical to the saved results, byte for byte. Only `run_receipt.json` changes between runs, because it records the time and the code hash. The `command` text inside the saved receipt shows the path that was used when the video was recorded; in this repository the command is `python code/target_manifest_demo.py`.

Data licences: UniProt is CC BY 4.0, PDB archive data is CC0, ChEMBL is CC BY-SA 3.0 (credit ChEMBL/EMBL-EBI).
