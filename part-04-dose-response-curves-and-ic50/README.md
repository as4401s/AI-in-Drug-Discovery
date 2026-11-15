# Part 4: Dose-response curves and IC50

Code for the fourth video of the course. The video shows how a row of plate-reader signals becomes a dose-response curve, how a curve becomes an IC50, and why a number copied from a database becomes a label only after curation. Two scripts do the work: one fits a clearly labelled **synthetic** curve, the other curates twelve **real** ChEMBL records for erlotinib on EGFR and keeps every assay in its own group.

The video explains what the code does and why, starting from everyday pictures and tiny worked numbers. The line-by-line reading lives in the commented files in this folder, and the Medium article walks through the same steps in writing.

## What is in this folder

| Path | What it is |
|------|------------|
| `code/dose_response_lab.py` | The synthetic-data lab: normalization, a small readable Hill-curve fit, refusal rules, a bootstrap interval and the lesson's failure cases. Every step has a comment that explains what it does and why. |
| `code/curate_activities.py` | The curation of twelve real ChEMBL records, with a written reason for every exclusion. |
| `code/worked_examples.py` | The small calculations from the video, step by step: the bakery line and percent inhibition, syrup concentrations, the staircase of units, tenfold and threefold dilutions, the start and finish lines of a plate, three wells against three days, the Hill formula in six steps, the slope table, relative and absolute 50 %, potency against efficacy, Cheng-Prusoff, pIC50, residuals and RMSE, a coarse-to-fine search, the bootstrap hat, bracketing, GR values, six invented activity rows, a bound at the top of the ruler and the three exercises. Standard library only; the last section compares the numbers with the real functions of `dose_response_lab.py` when NumPy is installed. |
| `code/fetch_sources.py` | Downloads the public source files (ChEMBL records and background documents). |
| `code/test_dose_response_lab.py` | Ten offline checks of the lab. |
| `code/test_curate_activities.py` | Seven offline checks of the curation rules on real records. |
| `data/raw/` | The saved inputs: the Part 3 manifest (`episode03-target_reference_manifest.v1.json`) and its hash file, and the saved ChEMBL records (209 activity rows, plus the assay and paper records of the twelve selected ones). |
| `research/download_receipts.json` | For every source file: where it came from, when, its size and SHA-256 hash. |
| `data/outputs/` | The results of the runs shown in the video: the synthetic wells, fit, bootstrap and failure cases, the curation table (JSON and CSV) and two run receipts. |

## What the scripts do

`dose_response_lab.py`

1. Checks that the Part 3 manifest is unchanged (EGFR, erlotinib).
2. Makes nine concentrations x three technical wells of fake signal around a known curve (midpoint 10 nM, slope 1), plus control wells.
3. Normalizes the signal to percent inhibition and keeps values outside 0 to 100 visible.
4. Fits a Hill curve (midpoint and slope, plateaus fixed at 0 and 100 percent) with a small explicit search, so every step can be read.
5. Flags or refuses fits that need a caution before any IC50 is reported, bootstraps the wells for a 95 percent interval, and shows the failure cases.

`curate_activities.py`

1. Re-checks the hash of every saved source file and the exact compound and target identity.
2. Joins each of the twelve selected activities to its assay and paper and checks that they agree.
3. Gives each record a status with written reasons: censored, missing, cell-based, mutant, unknown variant, duplicate, low target confidence, or retained.
4. Computes pIC50 only for exact values and cross-checks it against ChEMBL's pChEMBL value.

## What you should see

| Quantity | Value |
|----------|-------|
| Synthetic fit | accepted for teaching: IC50 about 9.78 nM, pIC50 about 8.01, Hill slope about 1.00 |
| Fit error | RMSE about 0.45 percentage points (a flat baseline would score about 39) |
| Bootstrap 95% interval | about 9.3 to 10.3 nM, all 400 resamples accepted |
| Real records | 209 source rows, 12 selected, exactly 1 retained (activity 13852013, IC50 2.6 nM, confidence score 9) |
| Excluded | 2 censored, 2 cell-based, 2 possible duplicates, 2 unknown variant, 1 missing value, 1 T790M mutant, 1 low target confidence |
| Assay groups | every assay kept in its own group |

The interval only describes technical-well noise on synthetic data. The curated records are literature measurements as ChEMBL holds them; each one stays in its own assay group, exactly as reported.

## How to run the worked examples

```
python code/worked_examples.py
```

It prints every small calculation from the video with its numbers: 40 % inhibition from 100 rolls to 60, 4,000 nM as 4 uM, a threefold series of 1000, 333.3, 111.1, 37.0 and 12.3, a test well of 550 as 50 % inhibition, a spread of 2 for three wells against 11.5 for three days, 9 %, 50 % and 91 % at 1, 10 and 100 nM, 80 % at 20 nM from the Hill formula, a slope table (33.33, 20 and 5.88 % at 5 nM), an absolute crossing at 200 nM, IC50 values of 20, 50 and 100 nM for one Ki of 10 nM, pIC50 values of 6 to 9, an RMSE of 2.16 against 33.14 for a flat baseline, the lowest error at 10 nM (2.15), bootstrap draws with means of 49.33, 50.67, 50.67 and 50, a GR value of 0.414 for both cell lines, IC50 > 10,000 nM as pIC50 < 5, the average of 125 nM that mixes two assays, and the three exercise answers (pIC50 7, 20 %, one eligible row).

## How to run it

You need Python 3.10 or newer and NumPy (`pip install numpy`).

```
python code/dose_response_lab.py
python -m unittest discover -s code -p "test_dose_response_lab.py" -v
```

The curation script also hash-checks six background documents (two papers and four web pages) that you download once and keep outside this repository. Download them once, which needs internet access, and then run it:

```
python code/fetch_sources.py
python code/curate_activities.py
python -m unittest discover -s code -p "test_curate_activities.py" -v
```

`fetch_sources.py` keeps the saved ChEMBL files, downloads only the missing documents and records their hashes in `research/download_receipts.json`. Web pages change over time, so a freshly downloaded page can have a different hash from the one in the video; the receipt is updated to match.

## About the comments

The scripts were annotated for this tutorial. The comments and docstrings were added while every working line stayed as it was: the parsed syntax tree of each annotated file is identical to the file that produced the saved results (SHA-256 of that file, `dose_response_lab.py`: `27cbb3e88c493fa9215093b1fe48ef1b08ba4f1d3287249683711a4c19d0625e`; `curate_activities.py`: `08bc6184ff60d884b953ee6b87014481e43594136bce983caa76a96608f12224`). To check the annotated code, the ten lab tests and the seven curation tests were run and both scripts were run again on the saved data. The curation table (JSON and CSV), the synthetic wells and the main fit were identical to the saved results. The numbers of the deliberately unstable failure case (`bad_nonmonotonic_model`) and the individual bootstrap estimates differed only in the eighth significant digit or later (largest relative difference about 4 in 100 million), because the check was run with a newer NumPy version than the original run. The curation check ran on the saved ChEMBL files; the six background documents were unavailable in that environment, so their hash check was skipped there. The `command` text inside the saved receipts shows the path used when the video was recorded; in this repository run `python code/dose_response_lab.py` and `python code/curate_activities.py`.

Data licences: ChEMBL is CC BY-SA 3.0 (credit ChEMBL/EMBL-EBI and keep the share-alike terms).
