"""Turn a declared ChEMBL assay cohort into one trustworthy measurement per molecule.

What this file does
    * identity gives a molecule a stable name (canonical SMILES and InChIKey) and rejects mixtures.
    * validate keeps only exact, positive IC50 values in nanomolar from the declared target and assay.
    * curate groups the accepted rows by structure, then converts the median IC50 into pIC50 = 9 - log10(IC50 in nM).

What it needs
    Python 3.10 or newer and RDKit (to read the SMILES and write the InChIKey).

What to expect
    curate returns two lists: the curated molecules (one entry each) and the rejected rows with a written reason.
"""

from collections import defaultdict
from math import isfinite, log10
from statistics import median

from rdkit import Chem, rdBase


def identity(smiles):
    """Keep the reported stereochemistry and reject mixtures or invalid structures.

    Returns (canonical SMILES, InChIKey). The InChIKey is the identity used to join tables later.
    """
    # A salt or mixture contains a '.' between its parts, so it is not one connected structure.
    if not isinstance(smiles, str) or not smiles or "." in smiles:
        raise ValueError("needs one connected structure")
    # BlockLogs keeps RDKit's warnings out of the output while we test the structure.
    with rdBase.BlockLogs():
        molecule = Chem.MolFromSmiles(smiles)
        key = Chem.MolToInchiKey(molecule) if molecule else ""
    if not key:
        raise ValueError("cannot obtain a valid structural identity")
    return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True), key


def validate(row, target, variant, allowed):
    """Accept exact positive nanomolar IC50 from the declared target and assay context.

    row: one activity record from ChEMBL. Returns the IC50 value as a number, or raises ValueError with the reason.
    """
    # The row has to come from the target and the assay we declared.
    if row["target_chembl_id"] != target or row["assay_chembl_id"] not in allowed:
        raise ValueError("different target or assay")
    # A mutant protein is a different experiment, so the variant has to match as well.
    if row["assay_variant_mutation"] != variant:
        raise ValueError("different target variant")
    # Keep only exact ('=') IC50 values in nanomolar; ranges such as '>' are not exact numbers.
    if [row["standard_type"], row["standard_relation"], row["standard_units"]] != ["IC50", "=", "nM"]:
        raise ValueError("needs exact IC50 in nanomolar")
    # ChEMBL marks doubtful rows with a validity comment or a duplicate flag.
    if row["data_validity_comment"] or row["potential_duplicate"] not in (0, None):
        raise ValueError("flagged activity")
    try:
        value = float(row["standard_value"])
    except (ValueError, TypeError) as error:
        raise ValueError("missing or invalid quantitative activity") from error
    # A logarithm needs a finite, positive concentration.
    if not isfinite(value) or value <= 0:
        raise ValueError("IC50 must be finite and positive")
    return value


def curate(activities, target, variant, allowed_assays):
    """Make one row per standard InChIKey and retain each supporting source activity.

    Returns (curated, rejected): curated molecules with their pIC50, and rejected rows with a reason.
    """
    # Every source activity ID should appear once; repeats would mean the download was damaged.
    if len({row["activity_id"] for row in activities}) != len(activities):
        raise ValueError("The retained response repeats a source activity ID")
    groups = defaultdict(list)
    rejected = []
    # Visit rows in activity-ID order so the result is the same on every run.
    for row in sorted(activities, key=lambda entry: entry["activity_id"]):
        try:
            value = validate(row, target, variant, allowed_assays)
            smiles, key = identity(row["canonical_smiles"])
        except ValueError as error:
            # Keep the reason, so every rejection can be explained later.
            rejected.append({"activity_id": row["activity_id"], "reason": str(error)})
            continue
        # Rows that describe the same structure end up in the same group.
        groups[key].append((row, smiles, value))

    curated = []
    for key, group in sorted(groups.items()):
        representative, smiles, _ = group[0]
        sources = [row for row, _, _ in group]
        concentrations = [value for _, _, value in group]
        curated.append({
            "inchikey": key,
            "smiles": smiles,
            "compound_id": representative["molecule_chembl_id"],
            "compound_ids": sorted({row["molecule_chembl_id"] for row in sources}),
            "target_id": target,
            "variant": variant,
            "assay_ids": sorted({row["assay_chembl_id"] for row in sources}),
            "source_activity_ids": [row["activity_id"] for row in sources],
            "observed_ic50_nm": concentrations,
            # pIC50 = 9 - log10(IC50 in nM); several measurements of one structure are summarised by their median.
            "pic50": median(9.0 - log10(value) for value in concentrations),
        })
    return curated, rejected
