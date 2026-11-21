# Rebuilt Chapter 7 sources

## Selected experimental inputs

- **EGFR** uses ChEMBL 37 [assay CHEMBL3705421](https://www.ebi.ac.uk/chembl/api/data/assay/CHEMBL3705421.json) and [document CHEMBL3638799](https://www.ebi.ac.uk/chembl/api/data/document/CHEMBL3638799.json), *Quinazoline derivatives as a multiplex inhibitor and method for the preparation thereof*, US-8846699-B2. The record assigns a human EGFR protein target and describes one ATP concentration and one kinase readout. It carries no variant annotation. The snapshot holds 173 exact nM activity rows and curation yields 170 unique structural identities.
- **KRAS G12D** uses ChEMBL 37 [assay CHEMBL5136563](https://www.ebi.ac.uk/chembl/api/data/assay/CHEMBL5136563.json) and Garrigou et al., *Accelerated Identification of Cell Active KRAS Inhibitory Macrocyclic Peptides using Mixture Libraries and Automated Ligand Identification System (ALIS) Technology*, J. Med. Chem. 65, 8961–8974 (2022). The assigned variant is human P01116 G12D. The exercise takes the documented recombinant protein nucleotide-exchange IC50 values. The snapshot holds 23 activities and 23 unique identities. The small challenge cohort can illustrate the method and its limitations. [Author paper](https://doi.org/10.1021/acs.jmedchem.2c00154)
- Both raw result pages, assay and document records are hash-bound in [COHORT_LOCK.json](../data/input/COHORT_LOCK.json). Measurements are scoped to their assay. The source dataset is [EMBL-EBI ChEMBL, CC BY-SA 3.0](https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/general-questions).

The development team selected a documented assay type, organism, target or variant, fixed assay context, exact positive nM IC50 values and enough distinct identities for a teaching run. A larger EGFR source named two ATP conditions that the retained activity fields could not disambiguate. A second large EGFR source described both wild-type and mutant measurements without explicit variant annotations in the queried records. Their discovery records remain in the research scout.

## Algorithms and evaluation

- [Breiman, Random Forests (2001)](https://link.springer.com/article/10.1023/A%3A1010933404324) for randomized trees and aggregation.
- [Chen and Guestrin, XGBoost (2016), author preprint](https://arxiv.org/abs/1603.02754) and the [official boosted-tree explanation](https://xgboost.readthedocs.io/en/stable/tutorials/model.html) for additive fitting and regularization.
- [Scikit-learn GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html) and [RDKit Murcko scaffold API](https://rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html) for disjoint group handling.
- [Gilmer et al., Neural Message Passing for Quantum Chemistry (2017)](https://proceedings.mlr.press/v70/gilmer17a.html) for atom message aggregation and graph readout. The local NumPy baseline is a smaller model with a single learned neighborhood layer and mean pooling.
- [Angelopoulos and Bates, conformal prediction (2021)](https://arxiv.org/abs/2107.07511) for the finite-sample calibration order statistic and assumptions. The teaching version applies it to the maximum magnitude of the error within each calibration group. Coverage on a different chemical population is an empirical question.
