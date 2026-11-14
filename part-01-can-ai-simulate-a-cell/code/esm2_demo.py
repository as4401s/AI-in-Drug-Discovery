"""ESM-2 masked-amino-acid experiment  (Part 1: "Can AI simulate a cell?")

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Reads a protein sequence (EGFR first, then KRAS) from a FASTA file.
  2. Cuts out a short window of that sequence around one amino-acid change:
     EGFR C797S (cysteine at position 797 becomes serine) and
     KRAS G12D (glycine at position 12 becomes aspartate).
  3. Turns the window into tokens and runs ESM-2, a small pretrained protein
     language model, on it. This is inference only: nothing is trained here.
  4. Saves the model's internal numbers: embeddings and attention weights.
  5. Hides ("masks") the amino acid at the position of interest and asks the
     model how likely each of the 20 amino acids is at that spot.
  6. Compares the probability of the changed amino acid with the original one.
     The result is a simple score called the masked-marginal log-odds.

WHAT YOU NEED
  * Python with numpy, torch and transformers installed.
  * The ESM-2 8M checkpoint (facebook/esm2_t6_8M_UR50D) saved on disk, plus the
    two FASTA files and the provenance file that the course folder provides.
  * The script runs offline: it never downloads anything.

WHAT YOU SHOULD SEE (values from the run shown in the video)
  EGFR C797S: P(C) = 0.0172, P(S) = 0.0735, score = +1.455  (S is about 4.3x more likely)
  KRAS G12D : P(G) = 0.0628, P(D) = 0.0284, score = -0.794  (G is favoured)
  Embeddings have shape (63, 320) for the 61-residue EGFR window (61 residues
  + 2 special tokens, 320 numbers per token). Attention has shape (6, 20, 63, 63).

HOW TO READ THE RESULT
  The score describes a preference of this small model inside a short window.
  It does not measure drug binding, resistance, cell growth or patient benefit.
"""
# Lets us write type hints such as tuple[str, str] on older Python versions.
from __future__ import annotations

# --- Imports from the Python standard library (they ship with Python) ---
# argparse reads command-line options, hashlib makes file fingerprints, json writes the results
# file, dataclasses gives us a tidy container, pathlib handles file paths, time measures how long we
# run.
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

# --- Third-party imports (install with pip) ---
# numpy stores and saves arrays of numbers, torch runs the neural network, transformers loads the
# ESM-2 tokenizer and model.
import numpy as np
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

# Folder layout: this script lives in <lesson>/code/, so the lesson folder is one level up and the
# course folder is one level above that.
LESSON = Path(__file__).resolve().parents[1]
COURSE = LESSON.parent
# The 20 standard amino acids, written with the one-letter codes used in protein sequences.
AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


# A small, read-only container describing the piece (window) of the protein that we feed to the
# model. Positions are 1-based in the full protein, the way biologists number them.
@dataclass(frozen=True)
class SequenceWindow:
    # Position of the amino acid of interest in the full protein, counting from 1.
    canonical_position: int
    # The original amino acid at that position (for EGFR C797S this is C, cysteine).
    wild_type: str
    # The amino acid that replaces it (for EGFR C797S this is S, serine).
    mutant: str
    # First and last position (1-based, inclusive) of the window cut from the full protein.
    start_position: int
    end_position: int
    # The amino-acid letters inside the window.
    sequence: str
    # Where the amino acid of interest sits inside the window, counting from 0 (Python style).
    residue_offset_zero_based: int


def sha256(path: Path) -> str:
    """Return the SHA-256 fingerprint of a file. Two files with the same fingerprint have identical
    contents, so we can prove that an input file did not change.
    """
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_fasta(path: Path) -> tuple[str, str]:
    """Read a FASTA file that holds exactly one protein and return (header, sequence)."""
    # Read the file, strip surrounding spaces and ignore blank lines.
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    # A FASTA record is one header line that starts with '>' followed by the sequence. We insist on
    # exactly one record so two proteins can never be mixed up.
    if not lines or not lines[0].startswith(">") or any(line.startswith(">") for line in lines[1:]):
        raise ValueError("Expected exactly one FASTA record")
    # The sequence may be wrapped over several lines; join them into one string.
    sequence = "".join(lines[1:])
    # Reject anything that is not one of the 20 standard amino-acid letters (this beginner example
    # does not handle unusual residues).
    if not sequence or set(sequence) - set(AMINO_ACIDS):
        raise ValueError("This beginner example expects the 20 standard amino acids")
    # Return the header (without the '>') and the sequence.
    return lines[0][1:], sequence


def select_window(sequence: str, position: int, wild_type: str,
                  mutant: str, radius: int = 30) -> SequenceWindow:
    """Cut a window of up to `radius` amino acids on each side of `position` and describe it.
    A window keeps the example small and fast on a CPU. It also limits the context the model sees,
    so every result must be described as 'this model on this window'.
    """
    # Check the inputs before using them: the position must lie inside the protein, and the letters
    # must be real amino acids.
    if not 1 <= position <= len(sequence):
        raise ValueError("Canonical residue position is outside this sequence")
    if radius < 0 or wild_type not in AMINO_ACIDS or mutant not in AMINO_ACIDS:
        raise ValueError("Expected a nonnegative radius and standard amino-acid letters")
    # Safety check: the letter at this position in the file must be the amino acid we expect (C at
    # 797 for EGFR). If not, we would be scoring the wrong change.
    if sequence[position - 1] != wild_type:
        raise ValueError(f"Position {position} is {sequence[position - 1]}, expected {wild_type}")
    # Take up to `radius` amino acids on each side. max() and min() stop the window from running off
    # either end of the protein. KRAS position 12 is near the start, so its window begins at
    # position 1 and is shorter on the left.
    start = max(1, position - radius)
    end = min(len(sequence), position + radius)
    # sequence[start - 1:end] converts 1-based numbering to Python's 0-based slicing. The last value
    # is where our amino acid sits inside the window, counting from 0.
    return SequenceWindow(position, wild_type, mutant, start, end,
                          sequence[start - 1:end], position - start)


def analyze_window(tokenizer, model, window: SequenceWindow,
                   output_dir: Path) -> dict[str, object]:
    """Run ESM-2 on one sequence window and return every number worth keeping.
    Two forward passes are made. The first sees the whole window and gives embeddings and attention.
    The second hides the amino acid of interest and gives probabilities for what could be there.
    """
    # STEP 1 - tokenize. The model works on integers, not letters. The tokenizer maps each amino-
    # acid letter to an integer id. add_special_tokens=True adds a start token <cls> and an end
    # token <eos>.
    encoded = tokenizer(window.sequence, return_tensors="pt", add_special_tokens=True)
    # Turn the ids back into readable labels so we can check what the model will see.
    token_ids = encoded["input_ids"][0].tolist()
    tokens = tokenizer.convert_ids_to_tokens(token_ids)
    # Sanity check 1: one token per amino acid plus <cls> at the start and <eos> at the end (61 + 2
    # = 63 tokens for the EGFR window).
    if tokens[0] != "<cls>" or tokens[-1] != "<eos>" or len(tokens) != len(window.sequence) + 2:
        raise ValueError("The expected one-residue-per-token ESM framing changed")
    # Sanity check 2: the tokens between <cls> and <eos> must be exactly our sequence, in the same
    # order.
    if tokens[1:-1] != list(window.sequence):
        raise ValueError("Tokenizer did not preserve the residue coordinates")
    # Where is our amino acid among the tokens? Its offset inside the window, plus 1 because <cls>
    # sits in front.
    target_index = window.residue_offset_zero_based + 1
    # Sanity check 3: the token at that index must be the original amino acid. This guards against
    # an off-by-one mistake that would make us hide the wrong position.
    if tokens[target_index] != window.wild_type:
        raise ValueError("Canonical position did not map to the intended model token")

    # The unmasked pass supplies real representations and raw attention weights.
    with torch.inference_mode():
        # STEP 2 - forward pass on the full, unmasked window. inference_mode() switches off gradient
        # tracking because we are only using the model, not training it. We also ask for the hidden
        # states (embeddings) and attention weights.
        unmasked = model(**encoded, output_hidden_states=True, output_attentions=True,
                         return_dict=True)
    # Embeddings: the last layer's list of 320 numbers for every token position (shape 63 x 320). An
    # embedding is how the model represents a position after reading its surroundings.
    embeddings = unmasked.hidden_states[-1][0].cpu().numpy()
    if unmasked.attentions is None:
        raise RuntimeError("This installed implementation did not return attention tensors")
    # Attention: for each of the 6 layers and 20 heads, a table that says how much every token looks
    # at every other token (shape 6 x 20 x 63 x 63). These are raw model weights, not a contact map
    # of the folded protein.
    attention = torch.stack([layer[0] for layer in unmasked.attentions]).cpu().numpy()
    # Sanity checks: no NaN or infinite values, and every row of attention weights must add up to 1
    # (attention weights are probabilities).
    if not np.isfinite(embeddings).all() or not np.isfinite(attention).all():
        raise RuntimeError("Non-finite model outputs")
    if not np.allclose(attention.sum(axis=-1), 1.0, atol=1e-5):
        raise RuntimeError("Unexpected attention normalization")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Save the arrays so they can be inspected later without running the model again.
    np.save(output_dir / "embeddings.npy", embeddings)
    np.save(output_dir / "attention.npy", attention)

    # Mask the residue before scoring both alternatives in the identical context.
    # STEP 3 - mask. Copy the input, then replace the token at our position with the model's special
    # <mask> token. clone() makes a real copy so the original input stays untouched.
    masked = {key: value.clone() for key, value in encoded.items()}
    masked["input_ids"][0, target_index] = tokenizer.mask_token_id
    with torch.inference_mode():
        # Forward pass on the masked input. The model returns one raw score (a logit) for every
        # symbol in its vocabulary at every position. We keep only the scores at the hidden
        # position.
        logits = model(**masked, return_dict=True).logits[0, target_index]
    # Softmax turns raw scores into probabilities that add up to 1. We keep the log-probabilities
    # too, because the variant score is a difference of logs.
    log_probability = torch.log_softmax(logits, dim=-1)
    probability = log_probability.exp()
    # Look up the vocabulary id of each of the 20 amino-acid letters. The vocabulary also contains
    # special tokens, so we pick out just the 20 we care about.
    aa_ids = [tokenizer.convert_tokens_to_ids(letter) for letter in AMINO_ACIDS]
    if len(set(aa_ids)) != 20 or tokenizer.unk_token_id in aa_ids:
        raise RuntimeError("Expected 20 distinct known amino-acid vocabulary items")
    # aa_mass is how much of the total probability sits on the 20 amino acids. aa_conditional re-
    # scales those 20 probabilities so that they add up to exactly 1. We keep both versions and
    # label them clearly.
    aa_mass = probability[aa_ids].sum()
    aa_conditional = probability[aa_ids] / aa_mass
    if not torch.isclose(probability.sum(), torch.tensor(1.0), atol=1e-6):
        raise RuntimeError("Vocabulary probability does not sum to one")
    if not torch.isclose(aa_conditional.sum(), torch.tensor(1.0), atol=1e-6):
        raise RuntimeError("Amino-acid conditional probability does not sum to one")
    # A readable table: for every amino acid, its raw probability and its re-scaled probability.
    distribution = [
        {"amino_acid": letter, "vocabulary_token_id": token_id,
         "raw_vocabulary_probability": float(probability[token_id]),
         "probability_conditional_on_20_amino_acids": float(aa_conditional[i])}
        for i, (letter, token_id) in enumerate(zip(AMINO_ACIDS, aa_ids))
    ]
    # Vocabulary ids of the original (wild-type) and the changed (mutant) amino acids.
    wild_id = tokenizer.convert_tokens_to_ids(window.wild_type)
    mutant_id = tokenizer.convert_tokens_to_ids(window.mutant)
    # STEP 4 - the variant score (masked-marginal log-odds): ln P(mutant) - ln P(wild type), both
    # measured in the same masked window. Positive: the model gives the changed letter more
    # probability. Negative: it prefers the original. exp(score) is the probability ratio.
    score = float(log_probability[mutant_id] - log_probability[wild_id])
    # Collect everything into one dictionary that main() writes to results.json. Each key has a
    # plain name, so the file can be read without reading the code.
    return {
        "window": asdict(window),
        "input_shape": list(encoded["input_ids"].shape),
        "token_labels": tokens,
        "target_token_index_zero_based": target_index,
        "coordinate_explanation": "Canonical position is 1-based; subtract window start for a zero-based residue offset, then add one for <cls>.",
        "embeddings_shape": list(embeddings.shape),
        "embeddings_file": str((output_dir / "embeddings.npy").relative_to(LESSON)),
        "embeddings_sha256": sha256(output_dir / "embeddings.npy"),
        "embedding_scope": "Final-layer unmasked token representations, including <cls> and <eos>.",
        "attention_shape": list(attention.shape),
        "attention_axes": ["layer", "head", "query token", "key token"],
        "attention_file": str((output_dir / "attention.npy").relative_to(LESSON)),
        "attention_sha256": sha256(output_dir / "attention.npy"),
        "attention_scope": "Raw unmasked self-attention weights; these are not a protein contact map or structural proof.",
        "masked_input_token_labels": tokenizer.convert_ids_to_tokens(masked["input_ids"][0].tolist()),
        "raw_vocabulary_probability_sum": float(probability.sum()),
        "probability_mass_on_20_amino_acids": float(aa_mass),
        "amino_acid_probabilities": distribution,
        "top_five_amino_acids": sorted(distribution, key=lambda row: row["raw_vocabulary_probability"], reverse=True)[:5],
        "mutation": f"{window.wild_type}{window.canonical_position}{window.mutant}",
        "wild_type_raw_probability": float(probability[wild_id]),
        "mutant_raw_probability": float(probability[mutant_id]),
        "wild_type_negative_log_likelihood_nats": float(-log_probability[wild_id]),
        "masked_marginal_log_odds_nats": score,
        "mutant_to_wild_type_probability_ratio": math.exp(score),
        "score_definition": "ln P(mutant | masked window) - ln P(wild type | the same masked window)",
        "interpretation_limit": "A relative sequence-model preference in this short window. It does not establish protein function, drug resistance, binding affinity, safety or clinical response.",
    }


def main() -> None:
    """Load the model once, analyse EGFR C797S and KRAS G12D, and write results.json."""
    # Command-line option: where to save the outputs (default: <lesson>/data/esm2).
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=LESSON / "data/esm2")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    # Safety: keep every output inside the lesson folder.
    if not output_dir.is_relative_to(LESSON):
        raise ValueError("Keep demonstration outputs inside this lesson")
    # Start a timer so we can report how long the run took.
    began = time.perf_counter()
    # Make the run reproducible: a fixed number of CPU threads, a fixed random seed and
    # deterministic algorithms, so the same input always gives the same numbers.
    torch.set_num_threads(2)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    # The provenance file records exactly which model files and protein data were used, with their
    # SHA-256 fingerprints.
    provenance_path = COURSE / "production/MODEL_DATA_PROVENANCE.json"
    provenance = json.loads(provenance_path.read_text())
    model_dir = COURSE / provenance["local_model_directory"]
    # Verify that every frozen file is unchanged. If one differs, stop instead of producing results
    # from the wrong inputs.
    for row in provenance["files"] + provenance["protein_data"]:
        if sha256(COURSE / row["local_path"]) != row["sha256"]:
            raise RuntimeError(f"Frozen source changed: {row['local_path']}")
    # Load the tokenizer and the model from local files only: nothing is downloaded and no remote
    # code is run. .eval() switches the model to prediction mode, and attn_implementation="eager"
    # makes it return attention weights.
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True,
                                             trust_remote_code=False, token=False)
    model = AutoModelForMaskedLM.from_pretrained(
        str(model_dir), local_files_only=True, trust_remote_code=False,
        token=False, use_safetensors=True, attn_implementation="eager",
    ).to("cpu").eval()
    # The two proteins. Each tuple is (UniProt accession, protein name, position, original amino
    # acid, changed amino acid). EGFR C797S is the guided example in the video, KRAS G12D is the
    # challenge.
    examples = []
    for accession, protein, position, wild_type, mutant in [
        ("P00533", "EGFR", 797, "C", "S"),
        ("P01116", "KRAS", 12, "G", "D"),
    ]:
        # For each protein: read its sequence, cut the window, run the model, then add bookkeeping
        # details to the result.
        fasta_path = LESSON / "data" / f"{accession}.fasta"
        header, sequence = read_fasta(fasta_path)
        window = select_window(sequence, position, wild_type, mutant)
        result = analyze_window(tokenizer, model, window, output_dir / protein.lower())
        result.update({"protein": protein, "uniprot_accession": accession,
                       "fasta_header": header, "canonical_sequence_length": len(sequence),
                       "source_fasta_sha256": sha256(fasta_path)})
        examples.append(result)
    # The final report: model details, software versions, hardware and the results for both
    # proteins. Writing all of this down is what makes the run reproducible.
    report = {
        "status": "executed", "created_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": provenance["model_id"], "model_revision": provenance["revision"],
        "model_parameter_count": sum(p.numel() for p in model.parameters()),
        "model_config": {key: getattr(model.config, key) for key in [
            "hidden_size", "num_hidden_layers", "num_attention_heads", "vocab_size"]},
        "device": "cpu", "dtype": str(next(model.parameters()).dtype),
        "cpu_threads": torch.get_num_threads(), "seed": 0,
        "hardware": {"machine": platform.machine(), "platform": platform.platform()},
        "python": sys.version, "python_executable": sys.executable,
        "packages": {name: importlib.metadata.version(name) for name in [
            "torch", "transformers", "numpy", "safetensors", "huggingface-hub"]},
        "command": [sys.executable, str(Path(__file__).resolve()), "--output-dir", str(output_dir)],
        "elapsed_seconds": time.perf_counter() - began,
        "code_sha256": sha256(Path(__file__).resolve()),
        "provenance_sha256": sha256(provenance_path),
        "examples": examples,
        "teaching_only_loss_examples": [
            {"probability": p, "negative_log_likelihood_nats": -math.log(p)} for p in [0.2, 0.8]
        ],
        "scope": "Real pretrained ESM-2 inference on short canonical sequence windows, not full kinase-domain/whole-protein modeling, folding, contact prediction, drug discovery or clinical validation.",
        "network": "Offline local-files-only inference; no authentication or remote code",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    # Save the report as results.json and print a short summary on screen.
    (output_dir / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "model_revision": report["model_revision"],
                      "elapsed_seconds": report["elapsed_seconds"], "output": str(output_dir / "results.json"),
                      "examples": [{"protein": row["protein"], "mutation": row["mutation"],
                                    "window_length": len(row["window"]["sequence"]),
                                    "embeddings_shape": row["embeddings_shape"],
                                    "attention_shape": row["attention_shape"],
                                    "wild_type_raw_probability": row["wild_type_raw_probability"],
                                    "mutant_raw_probability": row["mutant_raw_probability"],
                                    "log_odds_nats": row["masked_marginal_log_odds_nats"]}
                                   for row in examples]}, indent=2))


# Run main() only when the file is executed directly (python esm2_demo.py), not when it is imported.
if __name__ == "__main__":
    main()
