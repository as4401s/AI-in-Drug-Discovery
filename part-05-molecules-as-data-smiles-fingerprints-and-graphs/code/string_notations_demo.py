#!/usr/bin/env python3
"""String notations demo: SMILES, SELFIES and SAFE side by side (Part 5, "Molecules as Data").

What this script does
---------------------
1. Writes a few molecules as SELFIES (a string made of tokens in square brackets) and
   turns each SELFIES string back into SMILES, to show the round trip is lossless.
2. Edits strings at random, one position at a time, and counts how many edited
   strings still describe a real molecule. SMILES edits often break the grammar or the
   valence rules. SELFIES edits always decode to a molecule that RDKit accepts.
3. Writes the same molecules as SAFE strings, which group a molecule into fragments, and
   decodes them back again.

What it needs
-------------
    pip install rdkit selfies safe-mol
The script reads one saved file, the 170 EGFR structures from the feature hand-off
(`../data/handoff/parquet/feature_rows/egfr_feature_rows.json`, or a path you pass with --rows).

What you should see
-------------------
A short report on screen and a JSON file with every number (default
`../data/outputs/string_notations_results.json`). The random edits use a fixed seed, so the
counts repeat exactly when you run the script again with the same package versions.
Our own run is saved in that file: 479 of 3,400 edited SMILES strings stay valid (14.1 %),
and all 3,400 edited SELFIES strings stay valid (selfies 2.1.1, RDKit 2026.09.2).

Why it is here
--------------
SELFIES and SAFE are overview topics in the video. This script lets you see their
tokens and strings on real molecules, and measure the "always valid" idea yourself.
The main lab of this part keeps using SMILES with RDKit.
"""

import argparse
import json
import random
from pathlib import Path

from rdkit import Chem, RDLogger

import selfies as sf

RDLogger.DisableLog("rdApp.*")  # keep the screen quiet when we feed RDKit broken strings

# A few molecules we also meet in the video: name -> SMILES.
DEMO_MOLECULES = {
    "ethanol": "CCO",
    "dimethyl ether": "COC",
    "acetic acid": "CC(=O)O",
    "benzene": "c1ccccc1",
    "lactic acid (one mirror image)": "C[C@H](O)C(=O)O",
    "erlotinib": "COCCOc1cc2ncnc(Nc3cccc(C#C)c3)c2cc1OCCOC",
}

EDITS_PER_MOLECULE = 20  # random single-position edits per molecule and notation
SEED = 7                 # fixed seed: the same edits every run


def canonical(smiles):
    """Return RDKit's canonical SMILES for a string, or None when RDKit cannot read it."""
    molecule = Chem.MolFromSmiles(smiles) if smiles else None
    return Chem.MolToSmiles(molecule) if molecule is not None else None


def selfies_round_trip(smiles):
    """SMILES -> SELFIES -> SMILES. Returns the SELFIES string, its tokens and whether the molecule survived."""
    text = sf.encoder(smiles)                      # SMILES to SELFIES
    tokens = list(sf.split_selfies(text))          # the separate bracketed units
    back = sf.decoder(text)                        # SELFIES back to SMILES
    return text, tokens, canonical(back) == canonical(smiles)


def random_smiles_edit(smiles, alphabet, rng):
    """Replace one random character of a SMILES string with another character from the alphabet."""
    position = rng.randrange(len(smiles))
    return smiles[:position] + rng.choice(alphabet) + smiles[position + 1:]


def random_selfies_edit(text, alphabet, rng):
    """Replace one random token of a SELFIES string with another token from the alphabet."""
    tokens = list(sf.split_selfies(text))
    tokens[rng.randrange(len(tokens))] = rng.choice(alphabet)
    return "".join(tokens)


def validity_experiment(smiles_list, seed=SEED, edits=EDITS_PER_MOLECULE):
    """Edit every molecule `edits` times in each notation and count the edits RDKit accepts."""
    rng = random.Random(seed)
    # The pool of characters (SMILES) and tokens (SELFIES) that the edits may pick from.
    smiles_alphabet = sorted({ch for s in smiles_list for ch in s})
    selfies_strings = [sf.encoder(s) for s in smiles_list]
    selfies_alphabet = sorted(sf.get_alphabet_from_selfies(selfies_strings))

    smiles_valid = selfies_valid = 0
    for smiles, text in zip(smiles_list, selfies_strings):
        for _ in range(edits):
            if canonical(random_smiles_edit(smiles, smiles_alphabet, rng)) is not None:
                smiles_valid += 1
            # SELFIES: decode first (this always gives a SMILES string), then let RDKit judge it.
            if canonical(sf.decoder(random_selfies_edit(text, selfies_alphabet, rng))) is not None:
                selfies_valid += 1
    total = len(smiles_list) * edits
    return {
        "molecules": len(smiles_list), "edits_per_molecule": edits, "total_edits": total, "seed": seed,
        "smiles_alphabet_size": len(smiles_alphabet), "selfies_alphabet_size": len(selfies_alphabet),
        "smiles_valid_edits": smiles_valid, "selfies_valid_edits": selfies_valid,
        "smiles_valid_fraction": round(smiles_valid / total, 4),
        "selfies_valid_fraction": round(selfies_valid / total, 4),
    }


def safe_demo(smiles_by_name):
    """Write molecules as SAFE strings (fragments joined by dots) and decode them back."""
    try:
        import safe
    except ImportError:
        return {"available": False, "note": "install safe-mol to run this part"}
    rows = {}
    for name, smiles in smiles_by_name.items():
        try:
            text = safe.encode(smiles)             # SAFE string: fragments separated by dots
            back = safe.decode(text)               # back to a SMILES string
            rows[name] = {
                "safe": text, "fragments": text.count(".") + 1,
                "round_trip_same_molecule": canonical(back) == canonical(smiles),
            }
        except Exception as error:                 # keep going: report which molecule failed and why
            rows[name] = {"error": type(error).__name__ + ": " + str(error)[:160]}
    return {"available": True, "molecules": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = Path(__file__).resolve().parent
    parser.add_argument("--rows", type=Path,
                        default=here.parent / "data" / "handoff" / "parquet" / "feature_rows" / "egfr_feature_rows.json",
                        help="JSON list of EGFR structures (field canonical_isomeric_smiles)")
    parser.add_argument("--out", type=Path, default=here.parent / "data" / "outputs" / "string_notations_results.json",
                        help="where the JSON file with every number is written")
    args = parser.parse_args()

    results = {"selfies_version": sf.__version__, "round_trip": {}}

    print("1. SMILES -> SELFIES -> SMILES")
    for name, smiles in DEMO_MOLECULES.items():
        text, tokens, same = selfies_round_trip(smiles)
        results["round_trip"][name] = {"smiles": smiles, "selfies": text, "tokens": len(tokens), "same_molecule": same}
        print(f"   {name:34s} {smiles:42s} -> {text}   ({len(tokens)} tokens, same molecule: {same})")

    print("\n2. Random edits on the 170 EGFR structures")
    rows = json.loads(args.rows.read_text())
    egfr_smiles = [row["canonical_isomeric_smiles"] for row in rows]
    results["edit_experiment"] = validity_experiment(egfr_smiles)
    e = results["edit_experiment"]
    print(f"   {e['total_edits']} edits per notation (seed {e['seed']}): "
          f"SMILES valid {e['smiles_valid_edits']} ({e['smiles_valid_fraction']:.1%}), "
          f"SELFIES valid {e['selfies_valid_edits']} ({e['selfies_valid_fraction']:.1%})")

    print("\n3. SAFE strings")
    results["safe"] = safe_demo(DEMO_MOLECULES)
    if results["safe"].get("available"):
        for name, row in results["safe"]["molecules"].items():
            print(f"   {name:34s} {row.get('safe', row.get('error'))}")

    args.out.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"\nSaved {args.out}")


if __name__ == "__main__":
    main()
