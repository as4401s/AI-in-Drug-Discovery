# Part 1: Can AI simulate a cell?

Code for the first video of the course. The video starts from the biology (cell, DNA, RNA, protein), states a research problem, explains how a model learns (training, loss, attention), and ends with a real code experiment: a small protein language model, ESM-2, scores an amino-acid change in EGFR.

Video: [Part 1 on YouTube](https://youtu.be/nmAcM4L4XhU)  
Article: [Can AI Simulate a Cell? on Medium](https://arjun-sarkar786.medium.com/can-ai-simulate-a-cell-biology-basics-and-a-first-protein-language-model-with-esm-2-2ae9087f40b0)

## What is in this folder

| Path | What it is |
|------|------------|
| `code/esm2_demo.py` | The experiment from Part 4 of the video. Every step has a comment that explains what it does and why. The video shows the result of each step but does not read the code line by line; this file is the place to read it slowly. |
| `code/worked_examples.py` | The small calculations from the video, step by step: the loss numbers, the one-knob gradient descent walk, the three-position attention example, and how to read the saved attention weights. Needs only numpy. |
| `data/esm2/results.json` | The results of the run shown in the video (probabilities, scores, shapes, model revision, software versions). |
| `data/esm2/egfr/attention.npy` | The attention weights saved for the EGFR window (6 layers x 20 heads x 63 x 63). |

## What the script does

1. Reads the EGFR sequence from a FASTA file and checks that position 797 is cysteine (C).
2. Cuts a 61-residue window (positions 767 to 827) around that position.
3. Turns the window into 63 tokens (61 residues plus a start and an end token) and runs ESM-2 (`facebook/esm2_t6_8M_UR50D`, 7.5 million parameters) on a CPU.
4. Saves the embeddings (63 x 320) and the attention weights.
5. Hides position 797 and asks the model for the probability of each of the 20 amino acids there.
6. Scores the change as `ln P(mutant) - ln P(wild type)` in the same masked window.
7. Repeats the same steps for KRAS G12D (the challenge in the video).

## What you should see

| Change | P(original) | P(changed) | Score | Reading |
|--------|-------------|------------|-------|---------|
| EGFR C797S | 0.0172 | 0.0735 | +1.455 | the model gives S about 4.3 times the probability of C in this window |
| KRAS G12D | 0.0628 | 0.0284 | -0.794 | the model prefers the original G in this window |

These numbers describe one small model on one short window. Drug binding, resistance and patient benefit are each measured with their own experiments, and the video explains how the score fits into that bigger picture.

## How to run the worked examples

```
python code/worked_examples.py
```

It prints every number used in the video (loss 1.61 and 0.22, the knob walk 0 to 0.6 to 1.08 to 1.46, attention weights of about 41, 20 and 38 percent) and a short summary of the saved EGFR attention weights.

## How to run the ESM-2 experiment

You need Python 3.12 or newer with `numpy`, `torch` and `transformers`, the ESM-2 8M checkpoint saved on disk, the two FASTA files (UniProt P00533 for EGFR and P01116 for KRAS) in `data/`, and the provenance file `production/MODEL_DATA_PROVENANCE.json` from the course folder. The script never downloads anything: it loads the model from local files only and stops if a file's SHA-256 fingerprint has changed.

```
python code/esm2_demo.py --output-dir data/esm2
```

## About the comments

The script was annotated for this tutorial. The comments and docstrings were added without changing any working line: the parsed syntax tree of the annotated file is identical to the file that produced `results.json`, whose SHA-256 is `e1c5164c214f36dc75b995bfc6b821014363be5c54f79f662e83dd5f90b24f1c`. The model itself was not re-run when the comments were added.
