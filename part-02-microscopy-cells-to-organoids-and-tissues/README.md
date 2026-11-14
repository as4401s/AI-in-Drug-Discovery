# Part 2: Microscopy, from cells to organoids and tissues

Code for the second video of the course. The video follows the chain from light to image, from image to measurement, and from measurement to a carefully limited conclusion. The code turns a real fluorescence image into a measurement table with a transparent classical method (no AI model).

Video: [Part 2 on YouTube](https://youtu.be/YD-tiKCHg58)  
Article: [From Microscope Images to Measurements on Medium](https://arjun-sarkar786.medium.com/from-microscope-images-to-measurements-fluorescence-organoids-and-a-python-segmentation-baseline-6ec4ecdf5ada)

## What is in this folder

| Path | What it is |
|------|------------|
| `code/microscopy_demo.py` | The experiment from Part 3 of the video. Every step has a comment that explains what it does and why. |
| `data/cells3d-with-metadata.tif` | The image: Allen Institute for Cell Science "cells3d" (60 depth planes x 2 channels x 256 x 256), CC0, from the scikit-image sample data. |
| `code/outputs/` | The results of the run shown in the video: `results.json`, `nuclear_region_measurements.csv`, `image_metadata.json`. |
| `animation/` | The code that draws the animated visuals of the video. |

## What the script does

1. Loads the image stack and checks its fingerprint, channel order and pixel size (0.26 micrometres).
2. Picks depth plane 30 of the nuclei channel.
3. Chooses a threshold with Otsu's method and groups touching bright pixels into regions (8-connected components).
4. Removes regions smaller than 100 pixels and regions that touch the image border.
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

These regions are proposals made by an algorithm on one specimen. No expert-drawn reference was used, so the masks are not validated.

## How to run it

You need Python 3 with `numpy` and `Pillow`, `data/cells3d-with-metadata.tif`, and `data/cells3d-original-channel-order.tif` (the unmodified scikit-image copy, used to check the channel order). The overlay pictures use the macOS font `/System/Library/Fonts/Avenir.ttc`; on another system change that path in `save_display` and `main` to any TrueType font.

```
python code/microscopy_demo.py
```

## About the comments

The script was annotated for this tutorial. The comments and docstrings were added without changing any working line: the parsed syntax tree of the annotated file is identical to the file that produced the saved results (SHA-256 of that file: `3473d60f1199d8f1c137a8a271689117f915a4b510122d29ae7f34d7a2baf8af`). To check the annotated code, its functions were run on the image: the threshold, region counts, first region, both stress tests, the projection and the three built-in sanity checks all reproduced the numbers above. The full script was not re-run, because the second image file was not available at that moment.

Animation code uses the tools in [`../shared/animation-kit`](../shared/animation-kit).
