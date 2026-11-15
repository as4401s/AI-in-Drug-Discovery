#!/usr/bin/env python3
"""worked_examples.py - the small calculations from Part 2 of the video, reproduced step by step.

What it does
    The video builds each hard idea from an everyday picture and a tiny example with numbers you can repeat on a
    calculator. This script runs the same examples, so you can check every number and then change the inputs:

      1. Bit depth:            how many brightness levels a pixel can hold
      2. Image shape:          reading (depth, channel, row, column) as an address
      3. Brightness and units: why settings travel with the number
      4. Background and saturation: subtract an offset, and meet the top reading of the detector
      5. Pixels to micrometers: width of the picture, a scale bar, and the area of a pixel
      6. Depth:                where plane 30 sits in the z stack
      7. Maximum projection:   keep the brightest value at every position
      8. Otsu's threshold:     try every line, score each one, keep the best
      9. Connected regions:    edge neighbors versus edge-and-corner neighbors
     10. Measuring one region: area and mean intensity by hand
     11. Overlap:              intersection over union on a grid of squares
     12. Merges and splits:    why a high overlap can still give a wrong count
     13. Held-out data:        shuffled crops versus whole images, and wells as the biological unit
     14. Controls:             a fixed threshold meeting dimmer nuclei

What it needs
    Python 3.9 or newer and numpy. Nothing is downloaded and no image is opened.

What to expect
    The numbers printed below match the video (rounded):
      bit depths 256, 4096, 65536 levels          picture width 66.56 micrometers
      plane 30 sits 8.7 micrometers from plane 0   projection [5, 9, 8]
      Otsu line for the 8-pixel example: any line from 26 up to 199 separates the two piles best
      one 6-pixel region: area 0.4056 square micrometers, mean intensity 12500
      overlap 6 / 10 = 0.6                         edge rule 4 objects, edge-and-corner rule 2 objects

Run it from the folder that holds `code/` and `data/`:
    python code/worked_examples.py
"""
import numpy as np


def bit_depth_levels():
    """Part 1: a pixel stores a whole number, and the bit depth decides how many different numbers fit."""
    print("1. Bit depth: levels = 2 ** bits")
    for bits in (8, 12, 16):
        levels = 2 ** bits
        # the numbers start at 0, so the largest number a pixel can hold is levels - 1
        print(f"   {bits:2d}-bit image: {levels:6d} levels, from 0 to {levels - 1}")
    print("   Our image is stored as 16-bit whole numbers, so the largest value is 65535.\n")


def image_shape_as_address():
    """Part 1: the stack has the shape (60, 2, 256, 256) = (depth planes, channels, rows, columns)."""
    print("2. Reading the shape of an image stack as an address")
    shape = (60, 2, 256, 256)
    names = ("depth planes", "channels", "rows", "columns")
    for name, size in zip(names, shape):
        print(f"   {size:4d} {name}")
    # a tiny stand-in array with the same layout (all zeros) shows what the address selects
    stack = np.zeros(shape, dtype=np.uint16)
    sheet = stack[30, 0]   # depth plane 30, channel 0 (the nuclei channel in our file)
    print(f"   stack[30, 0] selects one sheet of squared paper with shape {sheet.shape}\n")


def brightness_and_units():
    """Part 1: arbitrary units compare well inside one session; settings must travel with the number."""
    print("3. Brightness with a scale that has no unit label")
    sample_a, sample_b = 1200, 2400
    print(f"   sample B / sample A = {sample_b / sample_a:.1f}  (same session, same settings: a real comparison)")
    print("   Sample A again with double the exposure reads 2400, the same as B: the settings changed the reading.\n")


def background_and_saturation():
    """Part 1: subtract a steady offset to restore a ratio; a full detector hides differences at the top."""
    print("4a. Background: raw readings versus true signals")
    background, dim_raw, bright_raw = 200, 1200, 2200
    print(f"   raw ratio              {bright_raw / dim_raw:.2f}")
    print(f"   after subtracting {background}: {(bright_raw - background) / (dim_raw - background):.2f}")
    print("4b. Saturation: a 12-bit detector tops out at 4095")
    top = 2 ** 12 - 1
    would_be = [3000, 5000, 9000]
    recorded = [min(v, top) for v in would_be]   # anything above the top reading is recorded as the top reading
    print(f"   would produce {would_be}  ->  recorded {recorded}")
    print("   The second and third structures now look equal: that difference is gone from the data.\n")


def pixels_to_micrometers(pixel_size=0.26, width_px=256):
    """Part 1: the pixel size turns pixel counts into physical lengths and areas."""
    print(f"5. Pixel size {pixel_size} micrometers")
    print(f"   picture width = {width_px} x {pixel_size} = {width_px * pixel_size:.2f} micrometers")
    print(f"   a 100-pixel scale bar = {100 * pixel_size:.0f} micrometers")
    print(f"   one pixel covers {pixel_size * pixel_size:.4f} square micrometers\n")


def depth_in_the_stack(planes=60, spacing=0.29):
    """Part 2: planes are spaced 0.29 micrometers apart; the first plane is plane 0."""
    print("6. Depth in the z stack")
    print(f"   {planes - 1} gaps x {spacing} = {(planes - 1) * spacing:.2f} micrometers from first to last plane")
    print(f"   plane 30 sits {30 * spacing:.1f} micrometers from plane 0\n")


def maximum_projection():
    """Part 2: keep the brightest value at every position, looking straight down through the pile."""
    print("7. Maximum-intensity projection of three sheets with three pixels each")
    sheets = np.array([[2, 9, 1], [3, 4, 8], [5, 2, 1]])
    projection = sheets.max(axis=0)   # axis 0 runs through the pile of sheets
    which_sheet = sheets.argmax(axis=0) + 1
    print(f"   sheets      {sheets.tolist()}")
    print(f"   projection  {projection.tolist()}  (the brightest value came from sheets {which_sheet.tolist()})\n")


def otsu_by_hand():
    """Part 3: try every possible line between the two piles and keep the best separation (Otsu's idea)."""
    print("8. Otsu's idea on eight pixels")
    values = np.array([20, 22, 24, 26, 200, 210, 220, 230])
    for line in (100, 23):
        dark, bright = values[values <= line], values[values > line]
        print(f"   line at {line:3d}: dark pile {len(dark)} pixels (mean {dark.mean():.0f}), "
              f"bright pile {len(bright)} pixels (mean {bright.mean():.0f}), means differ by {bright.mean() - dark.mean():.0f}")
    # Otsu scores every line with: weight_dark * weight_bright * (mean_dark - mean_bright) ** 2
    best_score, best_lines = -1.0, []
    for line in sorted(set(values.tolist()))[:-1]:
        dark, bright = values[values <= line], values[values > line]
        w0, w1 = len(dark) / len(values), len(bright) / len(values)
        score = w0 * w1 * (dark.mean() - bright.mean()) ** 2
        if score > best_score + 1e-9:
            best_score, best_lines = score, [line]
        elif abs(score - best_score) <= 1e-9:
            best_lines.append(line)
    print(f"   best score {best_score:.1f}; the best line sits after the value {best_lines[0]}, "
          f"so any line from {best_lines[0]} up to 199 separates the two piles equally well\n")


def label_neighbors(grid, eight_connected):
    """Count connected groups of 1s with a simple flood fill. Neighbors share an edge, or an edge or a corner."""
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if eight_connected:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, count = set(), 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1 and (r, c) not in seen:
                count += 1            # a new patch of land gets a new number
                stack = [(r, c)]
                while stack:          # paint everything connected to it
                    y, x = stack.pop()
                    if (y, x) in seen:
                        continue
                    seen.add((y, x))
                    for dy, dx in steps:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == 1 and (ny, nx) not in seen:
                            stack.append((ny, nx))
    return count


def counting_islands():
    """Part 3: a 6 x 6 grid with a solid square of four pixels and a diagonal of three pixels."""
    print("9. Counting islands: the neighbor rule changes the count")
    grid = [[0] * 6 for _ in range(6)]
    for r, c in [(1, 0), (1, 1), (2, 0), (2, 1)]:      # the solid square
        grid[r][c] = 1
    for r, c in [(3, 3), (4, 4), (5, 5)]:              # the diagonal: each pixel touches the next only at a corner
        grid[r][c] = 1
    print(f"   edges only:           {label_neighbors(grid, False)} objects")
    print(f"   edges and corners:    {label_neighbors(grid, True)} objects  (our code uses this rule, eight-connectivity)\n")


def measure_one_region(pixel_size=0.26):
    """Part 3: area from the pixel count, mean intensity from the raw values."""
    print("10. Measuring one region by hand")
    raw = [10000, 11000, 12000, 13000, 14000, 15000]
    area_px = len(raw) * pixel_size ** 2
    print(f"   one pixel = {pixel_size ** 2:.4f} square micrometers; {len(raw)} pixels = {area_px:.4f} square micrometers")
    print(f"   mean raw intensity = {sum(raw)} / {len(raw)} = {sum(raw) / len(raw):.0f} arbitrary units\n")


def intersection_over_union():
    """Part 4: two 4 x 4 sheets of tracing paper, one shaded by the model and one by the expert."""
    print("11. Intersection over union")
    model = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3)}
    expert = {(0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 3)}
    both, either = model & expert, model | expert
    print(f"   model {len(model)} squares, expert {len(expert)} squares, shaded on both sheets: {len(both)}")
    print(f"   union = {len(model)} + {len(expert)} - {len(both)} = {len(either)}")
    print(f"   IoU = {len(both)} / {len(either)} = {len(both) / len(either):.1f}\n")


def merges_and_splits():
    """Part 4: object counts can be off by one while almost every selected pixel agrees."""
    print("12. Merges and splits")
    reference = 4
    print(f"   merge: two touching nuclei get one outline -> model reports {reference - 1}, reference has {reference}")
    print(f"   split: one nucleus gets two outlines       -> model reports {reference + 1}, reference has {reference}")
    print("   Score table per image: matched, merged, split, missed, extra.\n")


def held_out_data():
    """Part 4: the test set must hold data the model has never seen; wells are the biological unit."""
    print("13. Held-out data")
    images, crops_each = 10, 100
    total = images * crops_each
    print(f"   {images} images x {crops_each} crops = {total} crops")
    print(f"   shuffled split: 800 train / 200 test -> every test crop has close neighbors from the same image in training")
    print(f"   whole-image split: hold out 2 images -> {2 * crops_each} test crops from images the model has never seen")
    wells, cells_per_well = 3, 1000
    print(f"   {wells} wells x {cells_per_well} cells = {wells * cells_per_well} cells, but {wells} independent treatment experiments\n")


def controls_and_a_fixed_threshold():
    """Part 4: halving the brightness of nuclei changes the count when the threshold stays fixed."""
    print("14. A fixed threshold meeting dimmer nuclei")
    threshold = 120
    control = np.linspace(150, 250, 100)     # 100 nuclei, brightness 150 to 250
    treated = np.linspace(75, 125, 100)      # the same nuclei at about half the brightness
    print(f"   control well: {(control > threshold).sum()} of 100 nuclei above {threshold}")
    print(f"   treated well: {(treated > threshold).sum()} of 100 nuclei above {threshold}")
    print("   The drop in count comes from the analysis rule meeting dimmer nuclei: inspect overlays and compare brightness.\n")


if __name__ == "__main__":
    bit_depth_levels()
    image_shape_as_address()
    brightness_and_units()
    background_and_saturation()
    pixels_to_micrometers()
    depth_in_the_stack()
    maximum_projection()
    otsu_by_hand()
    counting_islands()
    measure_one_region()
    intersection_over_union()
    merges_and_splits()
    held_out_data()
    controls_and_a_fixed_threshold()
