# AI in Drug Discovery

Code that accompanies the **WhiskerBrief "AI in Drug Discovery"** video course. Every video has its own folder (`part-NN-…`) holding the code used in that video. Shared tooling lives in `shared/`.

| Part | Video | Folder | Article |
|------|-------|--------|---------|
| 1 | [Can AI simulate a cell?](https://youtu.be/6MPPidoDUdQ) | [`part-01-can-ai-simulate-a-cell`](part-01-can-ai-simulate-a-cell) | [Medium](https://arjun-sarkar786.medium.com/can-ai-simulate-a-cell-biology-basics-and-a-first-protein-language-model-with-esm-2-2ae9087f40b0) |
| 2 | [Microscopy: from cells to organoids and tissues](https://youtu.be/YD-tiKCHg58) | [`part-02-microscopy-cells-to-organoids-and-tissues`](part-02-microscopy-cells-to-organoids-and-tissues) | [Medium](https://arjun-sarkar786.medium.com/from-microscope-images-to-measurements-fluorescence-organoids-and-a-python-segmentation-baseline-6ec4ecdf5ada) |
| 3 | _coming soon_ | – | – |
| 4 | _coming soon_ | – | – |
| 5 | _coming soon_ | – | – |

## Layout

```
part-NN-<video-name>/
  README.md        what the video covers, what each folder contains, how to run it
  code/            the scripts used in the video, with beginner-level comments
  data/            small sample inputs needed to run the code
```

## Notes

- Every script opens with a plain-language header (what it does, what it needs, what to expect) and explains each step in comments, so you can adapt it for your own data.
- Some scripts still use the absolute paths of the machine they were built on. Change those paths to your own checkout before running them.
- Rendered videos, audio, slides, web pages and large data files are not stored here (see `.gitignore`).
