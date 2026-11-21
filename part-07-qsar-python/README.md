# AI in Drug Discovery 7: Train and Validate EGFR QSAR Models in Python

This folder holds the Python lab from **AI in Drug Discovery 7: Train and Validate EGFR QSAR Models in Python**. The lab joins the Part 5 feature table to measured EGFR potencies, compares a random identity split with a Bemis–Murcko scaffold split, tunes Random Forest, XGBoost and a multilayer perceptron, fits a molecular graph baseline, reads parity plots and metrics, calibrates a prediction interval, repeats the procedure on a small KRAS G12D set, and saves the exact ensemble that Part 8 reloads.

The code is commented for beginners: every script opens with a plain-language header, every function has a docstring and each step has a short comment. The video explains the ideas and the results; it does not read the code line by line. The illustrated Medium article walks through the code.

## What You Need

- Python 3.10 or newer. The saved run used Python 3.12.
- The libraries below, at the versions the saved model was built with (the reload step checks them):

```sh
pip install numpy==2.2.6 scipy==1.15.3 scikit-learn==1.7.2 xgboost==3.0.5 joblib==1.5.2 rdkit==2025.9.6 pyarrow==21.0.0 pillow
```

- The Part 5 handoff folder, which this repository already contains at `../part-05-molecules-as-data-smiles-fingerprints-and-graphs/data/handoff/parquet`. Part 5 explains how its Parquet feature tables are made.

## Folder Map

| Folder | What it holds |
| --- | --- |
| `code/` | The scripts and their tests (see the table below). |
| `data/input/` | The frozen ChEMBL 37 activity cohorts for EGFR (assay CHEMBL3705421) and KRAS G12D (assay CHEMBL5136563), `labels.json` with one pIC50 per structure, and `COHORT_LOCK.json` with SHA-256 fingerprints of every file. |
| `data/trained/` | The evaluation files for both targets, the saved EGFR ensemble (`egfr_qsar_model.joblib`), `MODEL_MANIFEST.json`, the three reload probes and the verification receipts. |
| `data/plots/` | The five parity plots drawn by `plot_results.py`. |
| `data/output/` | The output of `worked_examples.py`. |
| `data/research/` | The assay and document records that justify the two cohorts, and `SOURCES.md`. |

## The Scripts

| Script | What it does |
| --- | --- |
| `worked_examples.py` | Repeats the small hand calculations of the video (pIC50, a tree, a forest, a boosting round, one neural-network update, message passing on C–C–O, the metrics and the calibration rank). |
| `curate_assays.py` | Turns a declared ChEMBL assay cohort into one pIC50 per structure and lists every rejected row with a reason. |
| `model_inputs.py` | Builds the number table X (2,048 Morgan bits, 167 MACCS bits, 7 descriptors), joins the measurements y by InChIKey and finds the nearest known molecule. |
| `assay_tables.py` | Checks the receipts, loads the Parquet feature table and the labels, and adds the Bemis–Murcko scaffold of each molecule. |
| `evaluation.py` | Random and scaffold splits, the metrics (MAE, RMSE, R², Spearman) and the calibrated interval half-width. |
| `graph_model.py` | A small message-passing network in NumPy. |
| `train_models.py` | Tunes the models with cross-validation on development data only, scores them on the test set, calibrates the interval and saves the EGFR ensemble. |
| `saved_model.py` | Reloads the saved ensemble after verifying its SHA-256 fingerprint and library versions, and predicts with an interval and a support check. |
| `plot_results.py` | Draws the parity plots. |
| `verify_training.py` | Checks that the partitions never overlap, that the saved model reloads and, with `--repeat`, that a fresh training run reproduces every saved file byte for byte. |
| `test_*.py` | Unit tests for the pieces above. |

## Run It

From this folder:

```sh
python code/worked_examples.py                       # small numbers, a few seconds, needs only NumPy
python -m unittest discover -s code -p 'test_*.py' -v # unit tests
python code/saved_model.py data/trained/MODEL_MANIFEST.json   # reload the saved ensemble and check three probes
python code/verify_training.py                       # check the saved evaluation files
python code/train_models.py --output /tmp/qsar-run   # train everything again into a new folder (a few minutes)
python code/plot_results.py data/trained/egfr_evaluation.json data/plots --font DejaVuSans.ttf
```

`train_models.py` writes into `data/trained/` by default and replaces the saved files. Give it a different `--output` folder to keep the saved results untouched. `plot_results.py` needs the path of any TrueType font on your computer.

The only difference between these scripts and the ones shown in the video is where they look for their input folders and which font file the plots use; the working lines are the same.

## What You Should See

All numbers below come from the saved files in `data/trained/`.

- **EGFR, 170 molecules in 23 scaffolds.** The random identity split gives 102 development, 34 calibration and 34 test molecules. The scaffold split gives 142 development, 11 calibration and 17 test molecules, with no scaffold shared between sets.
- **Test MAE, random identity split:** median baseline 0.556, Random Forest 0.525, XGBoost 0.567, multilayer perceptron 0.598, graph baseline 0.556, ensemble 0.547.
- **Test MAE, scaffold split:** median baseline 0.481, Random Forest 0.615, XGBoost 0.628, multilayer perceptron 0.915, graph baseline 0.506, ensemble 0.640. On unfamiliar scaffolds the simple median predicts better than the models, which is the point of the scaffold exam.
- **The calibrated interval** on the scaffold split has half-width 1.617 pIC50 units and covered 16 of the 17 test molecules (4 of 5 test scaffolds).
- **KRAS G12D, 23 molecules in 17 scaffolds** is a small challenge set that illustrates the method and its limits; its scaffold test set has only 4 molecules.
- **The saved model** was trained on the 142 development molecules of the scaffold split. Its SHA-256 fingerprint is `0fb37847a2303f9af14683b36b5098344b8bb8ab8840bc00b113b361e2db90d1`, its support cutoff is a nearest-neighbor Tanimoto of 0.588 and Part 8 reloads exactly this file.
- `verify_training.py --repeat` recorded byte-identical results for all five artifacts on a fresh replay. The multilayer perceptron prints convergence warnings; they are expected for this small data set.

## Data Identity and Licence

The measurements come from ChEMBL 37 ([EMBL-EBI](https://www.ebi.ac.uk/chembl/), CC BY-SA 3.0): EGFR from assay [CHEMBL3705421](https://www.ebi.ac.uk/chembl/explore/assay/CHEMBL3705421) and KRAS G12D from assay CHEMBL5136563 ([Garrigou et al., 2022](https://doi.org/10.1021/acs.jmedchem.2c00154)). Each target uses one assay, and each molecule keeps one pIC50 (the median of its exact nanomolar IC50 values). Keep the attribution and share-alike terms when you redistribute the data. The frozen activity responses, assay records and document records sit in `data/input/`, and `COHORT_LOCK.json` records their SHA-256 fingerprints and request URLs. The larger discovery pages that were used to choose the two cohorts are not stored here.

A `.joblib` file can run code when it is loaded. `saved_model.py` loads the model only after the file's fingerprint matches the manifest, and you should apply the same rule to any model file you receive.

## Course Links

This lesson continues from [Part 6](../part-06-qsar-evaluation) (the ideas behind QSAR evaluation) and [Part 5](../part-05-molecules-as-data-smiles-fingerprints-and-graphs) (the feature handoff). [Part 8](../part-08-virtual-screening) reloads the saved ensemble. See the [course table](../README.md) for every lesson, video and article.
