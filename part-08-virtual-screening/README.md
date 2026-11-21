# AI in Drug Discovery 8: Virtual Screening and Chemical Diversity in Python

This folder holds the Python lab from **AI in Drug Discovery 8: Virtual Screening and Chemical Diversity in Python**. The lab reloads the exact EGFR ensemble saved in [Part 7](../part-07-qsar-python), scores a frozen library of 456 structures, applies a potency gate and a structural-support gate, clusters the candidates that pass both gates with Butina sphere exclusion, and chooses twenty proposals with the MaxMin rule. It then compares that list with the twenty highest scores and writes the twenty rows with their provenance.

The code is commented for beginners: every script opens with a plain-language header, every function has a docstring and each step has a short comment. The video explains the ideas and the results; it does not read the code line by line. The illustrated Medium article walks through the code.

## What You Need

- Python 3.10 or newer. The saved run used Python 3.12.
- The same library versions as Part 7, because the saved model checks them when it loads:

```sh
pip install numpy==2.2.6 scipy==1.15.3 scikit-learn==1.7.2 xgboost==3.0.5 joblib==1.5.2 rdkit==2025.9.6 pyarrow==21.0.0 pillow
```

- This repository's [Part 7](../part-07-qsar-python) folder (the saved model and `saved_model.py`) and [Part 5](../part-05-molecules-as-data-smiles-fingerprints-and-graphs) folder (`feature_handoff.py`). `screen_library.py` finds both by their folder names.

## Folder Map

| Folder | What it holds |
| --- | --- |
| `code/` | The scripts and their tests (see the table below). |
| `data/source/` | The frozen library `COMBINED_LIBRARY.json` (95 ChEMBL catalogue structures and 361 structure-only virtual analogues), its lock with SHA-256 fingerprints, and `LIBRARY.json`. |
| `data/output/` | `egfr_20_diverse_hits.csv` (the twenty rows with provenance), `SCREEN_REPORT.json`, `CANDIDATE_SCORES.json`, `worked_examples.json` and the verification receipts. |
| `data/plots/` | The three figures drawn by `plot_screen.py`. |
| `data/research/` | The catalogue plan, the source notes and the library lock with the request details. |

## The Scripts

| Script | What it does |
| --- | --- |
| `worked_examples.py` | Repeats the small calculations of the video: Tanimoto similarity and distance, a five-molecule distance table, Butina clusters and a MaxMin choice of three. |
| `selection.py` | `distance_matrix` (1 − Tanimoto), `butina_clusters` (sphere exclusion), `maxmin` (choose the candidate farthest from everything chosen) and `selection_summary`. |
| `screen_library.py` | The whole screen: reload the Part 7 model, score the library, apply both gates, cluster, select twenty and write the files. |
| `verify_screen.py` | Re-derives the eligible set, the clusters, every MaxMin step and the CSV from the saved scores, and replays the screen to check that the files are byte-identical. |
| `plot_screen.py` | Draws the comparison bars, the two 20 × 20 distance heat maps and the first three structures. |
| `test_screening.py` | Unit tests of the distance table, the clusters and the MaxMin updates. |

## Run It

From this folder:

```sh
python code/worked_examples.py                        # the small teaching numbers
python -m unittest discover -s code -p 'test_*.py' -v  # unit tests
python code/screen_library.py --output /tmp/screen-run # run the whole screen into a new folder
python code/verify_screen.py                           # audit the saved outputs and replay the screen
python code/plot_screen.py data/output data/plots      # draw the three figures (edit FONT in the script to name a font on your computer)
```

`screen_library.py` writes into `data/output/` by default and replaces the saved files, so give it another `--output` folder to keep the saved results untouched.

The only differences between these scripts and the ones used in the video are the folder names they search for Parts 5 and 7 and the font file of the figures; the working lines are the same.

## What You Should See

- **456 structures scored:** 95 ChEMBL catalogue structures and 361 virtual analogues made by single, rule-based edits (a hydrogen on an aromatic ring replaced by F, Cl or methyl, and terminal halogen swaps) of the 142 Part 7 development structures.
- **Gate 1, predicted pIC50 at least 7:** 163 structures. **Gate 2, nearest training structure with Tanimoto at least 0.588:** 365 structures. **Both gates:** 162 structures, which form 13,041 pairs.
- **Butina sphere exclusion at distance 0.20** gives 74 clusters (46 of them with a single member). MaxMin chooses twenty cluster centroids; the first is the highest predicted pIC50 and each next one is the candidate whose nearest chosen molecule is farthest away.
- **Two lists of twenty compared:** the MaxMin list has mean pair distance 0.550 and closest pair distance 0.385 with mean predicted pIC50 7.34. The score-only list has mean pair distance 0.428 and closest pair distance 0.115 with mean predicted pIC50 7.75. The diverse list gives up some predicted potency and gains structural coverage.
- **The twenty rows** in `egfr_20_diverse_hits.csv` have no measured potency. Each row keeps the compound ID, InChIKey, SMILES, predicted pIC50 with its interval, the nearest training structure, the cluster, the model and library fingerprints, and the status columns `cell_painting_status` and `admet_status`, which the later lessons fill in.
- `verify_screen.py` recorded 20 independently re-derived MaxMin steps and byte-identical replays of the CSV, the report and the scores.

## What the Library Is and Is Not

Every structure here is a **proposal for future testing**. The predicted pIC50 values come from a model trained on one assay of 142 development structures; they are estimates, and the interval of Part 7 describes the typical size of a miss on unfamiliar scaffolds. The virtual analogues carry course IDs (`V8V-…`), a traceable editing rule and a connectivity block that is absent from the target-wide ChEMBL activity index searched for this lesson (58,847 activity rows checked, recorded in `COMBINED_LIBRARY_LOCK.json`). Physical availability and experimental potency remain to be determined.

The ChEMBL 37 catalogue data are from [EMBL-EBI](https://www.ebi.ac.uk/chembl/) under CC BY-SA 3.0; keep the attribution and share-alike terms when you redistribute them. The raw catalogue pages are not stored here; the lock files record their fingerprints and request details.

## Course Links

[Part 7](../part-07-qsar-python) trains and saves the model; this part reloads it. The twenty identities carry forward into the later lessons on Cell Painting profiles and ADMET. See the [course table](../README.md) for every lesson, video and article.
