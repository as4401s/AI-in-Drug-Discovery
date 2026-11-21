# AI in Drug Discovery 6: QSAR, Potency Scores and Honest Evaluation

This offline NumPy companion reproduces the small calculations in **AI in Drug Discovery 6: QSAR, Potency Scores and Honest Evaluation**. The video explains the ideas step by step; this script makes every number inspectable. The upcoming Part 7 implements the empirical potency-model workflow.

The code is commented for beginners: every script opens with a plain-language header, every function has a docstring, and each step has a short comment saying what it does and why. The video does not read the code line by line; the illustrated Medium article walks through it.

## Run the Examples

You need Python 3.10 or newer and NumPy. The saved run used Python 3.12.12 and NumPy 2.5.4 (live run). From this part folder:

```sh
python code/worked_examples.py
python -m unittest discover -s code -p 'test_*.py' -v
```

The first command prints JSON and writes the same results to `data/outputs/`. The tests run offline with the included small input records. These commands need only NumPy and the Python standard library, and running the examples makes no network request.

## What You Should See

The script prints genuine JSON and writes the same deterministic payload (schema version 1.1.0) to `data/outputs/worked_examples.json`. It also writes `data/outputs/evaluation_plan.json`: the explicit **planned** Part 7 acquisition, identity, split, baseline, metric and coverage contract. That plan contains no invented dataset size, split grouping or empirical model result.

| Calculation | Expected Output |
| --- | --- |
| 10 / 100 / 1000 nM unit-conversion inputs | pIC50 8 / 7 / 6 |
| Inverse conversion of pIC50 8 / 7 / 6 | 10 / 100 / 1000 nM |
| Separate retained erlotinib IC50 2.6 nM | pIC50 8.585026652029182 |
| Loss bowl (w − 3)² at w = 0, 1, 2, 3 | losses 9, 4, 1, 0 |
| Slope 2(w − 3) at w = 0 and w = 5 | −6 and +4 |
| Learning rate 0.1 from w = 0, three updates | w 0 → 0.6 → 1.08 → 1.464; loss 9 → 5.76 → 3.6864 → 2.359296 |
| Learning rate 0.5 from w = 0 | lands on w = 3, loss 0 |
| Learning rate 1.1 from w = 0 | w 6.6 (loss 12.96), then −1.32 (loss 18.6624) |
| 1000 examples in batches of 100 | 10 updates per epoch |
| Boosting targets [4, 6, 8], share 0.5 | first prediction 6; remaining −2, 0, +2; new prediction 5, 6, 7 |
| Boosting targets [4, 6, 8], share 0.5, two rounds | round 0 predicts 6; round 1 predicts 5, 6, 7; round 2 predicts 4.5, 6, 7.5; the remaining difference halves each round |
| Training labels [5, 6, 7] | fitted mean 6 |
| That baseline on references [6, 7, 8] | MAE 1; RMSE 1.2909944487358056; R² −1.5 |
| Specified line 7 + 0.5x at x = −1, 0, 1 | predictions [6.5, 7, 7.5] |
| Those predictions on references [6, 7, 8] | MAE 0.3333333333333333; RMSE 0.408248290463863; R² 0.75 |
| Ranks [1, 2, 3, 4] against [1, 3, 2, 4] | Spearman 0.8 |
| Predictions two units above [6, 7, 8, 9] | Spearman 1; MAE 2; RMSE 2; R² −2.2 |
| One absolute error of 0.5 pIC50 units | concentration ratio 3.1622776601683795 |
| One absolute error of 2 pIC50 units | concentration ratio 100 |
| Centring training values 4, 6, 8 with the training mean | mean 6; centred −2, 0, +2; held-aside 10 becomes 4; all-four mean 7 shown for comparison |
| Bit sets {1, 3, 5} and {1, 5, 7} | Tanimoto 2/4 = 0.5 |
| Schematic neighbour similarities 0.8, 0.5, 0.2 | nearest distance 1 − 0.8 = 0.2 |
| Ethanol (6 positions on) and dimethyl ether (4 on), 1 shared | union 9; Tanimoto 1/9 ≈ 0.111; distance 8/9 ≈ 0.889 |
| Lactic acid mirror images (11 positions on each), 9 shared | union 13; Tanimoto 9/13 ≈ 0.692; distance 4/13 ≈ 0.308 |
| Schematic error by distance group (eight invented rows) | MAE 0.3, 0.45, 0.75, 1.15 |
| Ten invented references inside 90% intervals | 9 of 10 inside, coverage 0.9, row 3 outside |
| Leaf references [6, 8] | leaf mean 7 |
| Specified tree predictions [6, 7, 8] | forest average 7 |

The scaffold counts shown in the video (170 EGFR compounds in 23 Bemis–Murcko scaffolds, 130 of them in `c1ccc(Nc2ncnc3ccccc23)cc1`, 17 scaffolds with one compound each) come from the Part 7 run; they are saved in `part-07-qsar-python/data/trained/egfr_evaluation.json`.

Residuals consistently mean **prediction minus reference**. R² uses the evaluation references' mean, 7, in its denominator. The fitted baseline uses the training mean, 6. Keeping these quantities separate is the point of the example.

## Scope and Data Identity

All model, ranking, concentration-grid, neighbour, distance-group and interval examples are explicitly labelled arithmetic illustrations. The line's coefficients and the tree and forest predictions are specified to explain their mechanisms. They are teaching numbers rather than locally trained empirical QSAR models, measured benchmark results or experimental labels assigned to the Part 5 molecules. The small training-mean baseline is genuinely fitted to the specified numerical teaching training labels.

The one measured reference is separate: ChEMBL activity **13852013**, assay **CHEMBL3095060**, erlotinib **CHEMBL553**, complete Standard InChIKey **AAKJLRGGTJKAMG-UHFFFAOYSA-N**, endpoint IC50, relation `=`, value **2.6 nM**. It is retained from the Part 4 ChEMBL_37 snapshot. The assay describes wild-type EGFR in a baculovirus expression system, poly(Glu,Tyr) 4:1 substrate and a 60-minute ELISA. The exact construct sequence and ATP concentration remain unavailable. The article methods are reported as published, and each record keeps its own assay with no averaging across assays.

`data/raw/retained_erlotinib_reference.json` carries the raw-record and assay snapshot hashes, original source snapshot identity and limitations. The raw activity and complete retained assay metadata sit alongside it. [The source article](https://pubmed.ncbi.nlm.nih.gov/24183742/) and [ChEMBL activity record](https://www.ebi.ac.uk/chembl/api/data/activity/13852013.json) preserve the original source identities.

## Meaningful Checks

Sixteen tests guard invalid concentrations, inverse-unit round trips, the shared loss objective, the learning-rate paths, the batch and epoch count, the boosting round, training-only centring, unmatched or missing reference rows, constant-reference R², constant-vector Spearman, average ranks for ties, training-only baseline fitting, perfect ordering with large value errors, duplicate identities across partitions, the distance-group and interval-coverage examples, and the exact lesson calculations. Undefined metric values are serialized as JSON `null` with a reason, so a score always carries its meaning.

The identity guard compares verified identity keys supplied by a caller. Deriving those keys and defining salts, tautomers and stereochemistry belong to the chemistry curation policy. Keeping an exact identity in one partition leaves the chemical similarity between partitions to a separate check.

## Attribution

ChEMBL data: ChEMBL/EMBL-EBI, release ChEMBL_37, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Preserve attribution and share-alike terms for redistributed or adapted data. Original article text and figures have separate rights. The mathematical examples are original course teaching material. The raw activity and assay snapshots retain the measured record's source identity. The unit conversions and model scores above are teaching calculations.

## Course Links

**AI in Drug Discovery 6: QSAR, Potency Scores and Honest Evaluation** is the concepts lesson for this folder. Its video and illustrated article are being prepared; public links will be added after publication.

This lesson assumes basic coding skills and a little familiarity with machine learning. Part 5 supplies the molecular-representation background. The planned Part 7 lab will inspect a compatible multi-compound assay collection, fit suitable baselines and a model, and retain actual held-out predictions. The line, tree and forest in this part explain mechanisms through specified numerical examples.

See the [course table](../README.md) for earlier published lessons and articles.
