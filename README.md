# AI in Drug Discovery

Code that accompanies the **WhiskerBrief "AI in Drug Discovery"** video course. Every video has its own folder (`part-NN-…`) holding the code used in that video. Shared tooling lives in `shared/`.

| Part | Video | Folder | Article |
|------|-------|--------|---------|
| 1 | [AI in Drug Discovery 1: Biology, How Models Learn, Transformers and ESM-2](https://youtu.be/nmAcM4L4XhU) | [`part-01-can-ai-simulate-a-cell`](part-01-can-ai-simulate-a-cell) | [Medium](https://arjun-sarkar786.medium.com/can-ai-simulate-a-cell-biology-basics-and-a-first-protein-language-model-with-esm-2-2ae9087f40b0) |
| 2 | [AI in Drug Discovery 2: Microscopy, Organoids and Image Analysis in Python](https://youtu.be/zfbtHyErKKc) | [`part-02-microscopy-cells-to-organoids-and-tissues`](part-02-microscopy-cells-to-organoids-and-tissues) | [Medium](https://arjun-sarkar786.medium.com/from-microscope-images-to-measurements-fluorescence-organoids-and-a-python-segmentation-baseline-6ec4ecdf5ada) |
| 3 | AI in Drug Discovery 3: The Drug Discovery Pipeline, EGFR and KRAS G12D (video coming soon) | [`part-03-drug-discovery-targets-and-molecular-identity`](part-03-drug-discovery-targets-and-molecular-identity) | – |
| 4 | AI in Drug Discovery 4: Dose-Response Curves, IC50 and a Python Fit (video coming soon) | [`part-04-dose-response-curves-and-ic50`](part-04-dose-response-curves-and-ic50) | – |
| 5 | AI in Drug Discovery 5: Molecules as Data with SMILES, Graphs and Fingerprints (video coming soon) | [`part-05-molecules-as-data-smiles-fingerprints-and-graphs`](part-05-molecules-as-data-smiles-fingerprints-and-graphs) | – |

## Layout

```
part-NN-<video-name>/
  README.md        what the video covers, what each folder contains, how to run it
  code/            the scripts used in the video, with beginner-level comments
  data/            small sample inputs needed to run the code, and the saved results
  research/        (some parts) receipts for the downloaded source files
```

## Notes

- Every script opens with a plain-language header (what it does, what it needs, what to expect) and explains each step in comments, so you can adapt it for your own data.
- Some scripts still use the absolute paths of the machine they were built on. Change those paths to your own checkout before running them.
- Rendered videos, audio, slides, web pages and large data files are not stored here (see `.gitignore`).
