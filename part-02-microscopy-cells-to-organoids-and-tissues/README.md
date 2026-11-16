# Part 2: Microscopy, from cells to organoids and tissues

Code for the second video of the course. The video follows the chain from light to image, from image to measurement, and from measurement to a carefully limited conclusion. The code turns a real fluorescence image into a measurement table with a transparent classical method (a threshold and connected regions), which gives us a clear baseline before the course introduces learned image models.

Video: [AI in Drug Discovery 2: Microscopy, Organoids and Image Analysis in Python on YouTube](https://youtu.be/gHBcBv8qsrg)  
Article: [AI in Drug Discovery 2: Microscopy, Organoids and Image Analysis in Python on Medium](https://arjun-sarkar786.medium.com/from-microscope-images-to-measurements-fluorescence-organoids-and-a-python-segmentation-baseline-6ec4ecdf5ada)

The video explains what the code does and why. The line-by-line reading lives in the commented files in this folder, and the Medium article walks through the same steps in writing.

## What is in this folder

| Path | What it is |
|------|------------|
| `code/microscopy_demo.py` | The experiment from Part 3 of the video. Every step has a comment that explains what it does and why. The video shows the result of each step but reads no code line by line; this file is the place to read it slowly. |
| `code/worked_examples.py` | The small calculations from the video, step by step: bit depth, the shape of an image stack, background and saturation, pixel size and area, the z stack, a maximum projection, Otsu's threshold on eight pixels, counting connected regions, measuring one region, intersection over union, merges and splits, held-out data and a fixed threshold meeting dimmer nuclei. Needs only numpy. |
| `data/cells3d-with-metadata.tif` | The image: Allen Institute for Cell Science "cells3d" (60 depth planes x 2 channels x 256 x 256), CC0, from the scikit-image sample data. |
| `code/outputs/` | The results of the run shown in the video: `results.json`, `nuclear_region_measurements.csv`, `image_metadata.json`. |

## What the video covers

1. Light becomes a measurement: fluorescence, labels, the detector, a grid of numbers, channels, intensity in arbitrary units, background, saturation, pixel size and area.
2. Cells, organoids and tissues: three ways to study cells, fixed and live samples, preparation, optical sections, z stacks and maximum projections.
3. A real pixels-to-measurements experiment: the image and its axes, one plane, Otsu's threshold, connected regions, measurement of area and intensity, and two stress tests.
4. What a learned segmentation model adds and which evidence it still needs: how a model learns from examples, overlap (IoU), merges and splits, held-out data, synthetic images, controls and interpretation.

Overview-only items in the video (SynOrg and the patient-derived organoid screen) are linked from the description. The ideas of Cell Painting measurements return in lesson 9, and spatial measurements in tissue return in lesson 27.

## What the script does

1. Loads the image stack and checks its fingerprint, channel order and pixel size (0.26 micrometres).
2. Picks depth plane 30 of the nuclei channel.
3. Chooses a threshold with Otsu's method and groups touching bright pixels into regions (8-connected components).
4. Keeps regions of at least 100 pixels that sit fully inside the image, and removes the smaller ones and the ones that touch the border.
5. Measures each remaining region: area in square micrometres and mean raw intensity.
6. Runs two stress tests: halving every pixel value, and a maximum-intensity projection through the stack.
7. Saves the table, label images, overlay pictures, `results.json` and a run receipt.

## What you should see

| Quantity | Value |
|----------|-------|
| Otsu threshold | 10432 raw intensity units |
| Regions found before filtering | 92 (70 too small, 10 touching the border) |
| Regions kept | 12 |
| First kept region | 1346 pixels = 90.99 square micrometres, mean intensity 13530.7 |
| Half brightness, old threshold | 3 regions |
| Half brightness, threshold re-estimated (5216) | 12 regions |
| Maximum-intensity projection (threshold 14226) | 9 regions |

These regions are proposals made by an algorithm on one specimen. Expert-drawn reference masks are the next step for validation, and Part 4 of the video explains how that comparison is scored.

## How to run the worked examples

```
python code/worked_examples.py
```

It prints every small calculation from the video with its numbers: 256, 4096 and 65536 levels for 8, 12 and 16 bits; a picture width of 66.56 micrometres; plane 30 at 8.7 micrometres; the projection [5, 9, 8]; the Otsu means 23 and 215; 4 objects with the edge rule and 2 with the edge-and-corner rule; a 6-pixel region of 0.4056 square micrometres with mean 12500; IoU 6 / 10 = 0.6; and the control well where 100 of 100 nuclei pass a threshold of 120 while the half-brightness treated well keeps only 10.

## How to run the image experiment

You need Python 3 with `numpy` and `Pillow`, `data/cells3d-with-metadata.tif`, and `data/cells3d-original-channel-order.tif` (the unmodified scikit-image copy, used to check the channel order). The overlay pictures use the macOS font `/System/Library/Fonts/Avenir.ttc`; on another system change that path in `save_display` and `main` to any TrueType font.

```
python code/microscopy_demo.py
```

## About the comments

The script was annotated for this tutorial. The comments and docstrings were added without changing any working line: the parsed syntax tree of the annotated file is identical to the file that produced the saved results (SHA-256 of that file: `3473d60f1199d8f1c137a8a271689117f915a4b510122d29ae7f34d7a2baf8af`). To check the annotated code, its functions were run on the image: the threshold, region counts, first region, both stress tests, the projection and the three built-in sanity checks all reproduced the numbers above. Running the full script end to end needs the second image file in `data/` (see above).
