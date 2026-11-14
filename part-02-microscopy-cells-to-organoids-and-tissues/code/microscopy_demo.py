"""From pixels to measurements  (Part 2: "Microscopy: from cells to organoids and tissues")

This is a classical image-analysis baseline. It is NOT a trained AI model and it is NOT a
paper reproduction. It shows how a real fluorescence image becomes a table of measurements,
and how to question those measurements.

WHAT THIS SCRIPT DOES, STEP BY STEP
  1. Loads a 3-D fluorescence image stack (Allen Institute "cells3d", CC0 licence):
     60 depth planes x 2 channels (nuclei and membranes) x 256 x 256 pixels.
  2. Checks the file fingerprint, the channel order and the pixel size (0.26 micrometres).
  3. Picks one depth plane (index 30) of the nuclei channel.
  4. Chooses an intensity threshold with Otsu's method.
  5. Groups touching bright pixels into regions (connected components).
  6. Drops regions that are too small (< 100 pixels) or that touch the image border.
  7. Measures each region: area in square micrometres and mean raw intensity.
  8. Runs two stress tests: halving the brightness, and a maximum-intensity projection.
  9. Saves a CSV table, label images, overlay pictures, a results.json and a run receipt.

WHAT YOU NEED
  * Python with numpy and Pillow.
  * data/cells3d-with-metadata.tif and data/cells3d-original-channel-order.tif
    (the second file is the unmodified scikit-image copy used to verify the channel order).
  * The overlay pictures use the macOS font /System/Library/Fonts/Avenir.ttc; on another
    system change that path to any TrueType font you have.

WHAT YOU SHOULD SEE (values from the run shown in the video)
  Otsu threshold ............ 10432 raw intensity units
  Regions found ............. 92  (70 too small and 10 touching the border are removed)
  Regions kept .............. 12
  First kept region ......... 1346 pixels = 90.99 square micrometres, mean intensity 13530.7
  Half-brightness test ...... old threshold keeps 3 regions; a re-estimated threshold (5216) keeps 12
  Maximum-intensity projection keeps 9 regions (threshold 14226)

HOW TO READ THE RESULT
  Every region is a proposal made by an algorithm. No expert-drawn ground truth was used, so
  the masks are not validated, and the numbers describe this one specimen and plane only.
"""
from __future__ import annotations

# --- Imports ---
# deque is a fast queue. We use it to walk across touching pixels (see label_components).
from collections import deque
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

# numpy holds the image as arrays of numbers. Pillow (PIL) reads TIFF files and draws the overlay
# pictures.
import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

# Folder layout: this script sits in <lesson>/code/, so ROOT is the lesson folder one level up. All
# outputs are written to <lesson>/code/outputs.
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "code/outputs"
# Fingerprint (SHA-256) of the exact image file we analyse. If the file ever changes, the script
# stops instead of silently analysing a different image.
EXPECTED_SHA256 = "bd35a300fbe4c90da5707eaa8b08f8893cb00787d81371c339057e068589691c"
# Which depth plane to analyse. Counting starts at 0, so 30 is the 31st of the 60 planes. This is an
# analysis choice, so it is saved together with the results.
SLICE_Z = 30
# Regions smaller than this many pixels are treated as noise specks and dropped (100 pixels = 6.76
# square micrometres at 0.26 micrometres per pixel).
MIN_AREA_PX = 100


def sha256(path: Path) -> str:
    """Return the SHA-256 fingerprint of a file (identical contents give an identical fingerprint)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_stack(path: Path) -> tuple[np.ndarray, dict]:
    """Read a multi-page TIFF and return (stack, dimensions).
    The stack has the axes (depth Z, channel C, row Y, column X). `dimensions` holds the metadata we
    need: the number of frames, the pixel density and the acquisition notes.
    """
    # A multi-page TIFF stores 60 depth planes x 2 channels as 120 consecutive pages (frames).
    with Image.open(path) as image:
        # TIFF tag 270 is the image description, where the acquisition software keeps its notes as
        # key=value lines (number of channels, slices, spacing and so on).
        description = str(image.tag_v2.get(270, ""))
        metadata = dict(line.split("=", 1) for line in description.splitlines() if "=" in line)
        # Tags 282 and 283 hold the pixel density: pixels per micrometre in x and y. We use them to
        # turn pixels into physical units.
        dimensions = {
            "frames": image.n_frames,
            "size_xy_px": list(image.size),
            "pixel_mode": image.mode,
            "description": description,
            "x_resolution_px_per_um": float(image.tag_v2.get(282)),
            "y_resolution_px_per_um": float(image.tag_v2.get(283)),
            "metadata": metadata,
        }
        # Read every page into a 16-bit unsigned integer array. These are the raw detector values (0
        # to 65535).
        frames = []
        for frame in range(image.n_frames):
            image.seek(frame)
            frames.append(np.array(image, dtype=np.uint16))
    # Re-shape the flat list of 120 pages into a 4-D array with axes (Z, C, Y, X) = (60, 2, 256,
    # 256). Shape tells us the arrangement; the metadata tells us what the arrangement means.
    channels = int(metadata["channels"])
    depths = int(metadata["slices"])
    stack = np.stack(frames).reshape(depths, channels, *frames[0].shape)
    return stack, dimensions


def otsu_threshold(image: np.ndarray) -> int:
    """Choose the split maximizing between-class variance of a uint16 histogram."""
    if image.dtype != np.uint16 or image.size == 0:
        raise ValueError("Otsu input must be a nonempty uint16 array")
    # Count how many pixels have each possible value from 0 to 65535. This is the histogram.
    histogram = np.bincount(image.ravel(), minlength=65536).astype(np.float64)
    # For every candidate threshold t, the running totals tell us how many pixels (count_low) and
    # how much total brightness (weighted_low) lie at or below t.
    count_low = np.cumsum(histogram)
    weighted_low = np.cumsum(histogram * np.arange(65536, dtype=np.float64))
    count_all = count_low[-1]
    # Otsu's score for a threshold is the between-class variance. It is large when the dark group
    # and the bright group are far apart and both well populated. Thresholds that leave one group
    # empty are skipped (denominator 0).
    denominator = count_low * (count_all - count_low)
    # Float64 prevents overflow when squaring the between-class numerator.
    score = np.divide(
        (weighted_low[-1] * count_low - weighted_low * count_all) ** 2,
        denominator,
        out=np.zeros(65536),
        where=denominator > 0,
    )
    # The best threshold is the one with the highest score.
    return int(np.argmax(score))


def label_components(mask: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    """Label eight-connected bright regions, retaining small/edge flags for QC."""
    # Connected-component labelling by flood fill: start at an unlabelled foreground pixel and
    # spread to every touching foreground pixel. All pixels reached share one label (1, 2, 3 ...).
    height, width = mask.shape
    labels = np.zeros(mask.shape, dtype=np.uint16)
    objects = []
    # Visit every foreground pixel (every True in the mask).
    for y, x in np.argwhere(mask):
        y, x = int(y), int(x)
        if labels[y, x] != 0:
            continue
        label = len(objects) + 1
        # Breadth-first search: keep a queue of pixels whose neighbours still have to be checked.
        queue = deque([(y, x)])
        labels[y, x] = label
        points = []
        while queue:
            row, column = queue.popleft()
            points.append((row, column))
            # Look at all 8 neighbours (the 3 x 3 block around the pixel): up, down, left, right and
            # the four diagonals. This rule is called 8-connectivity.
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = row + dy, column + dx
                    if 0 <= yy < height and 0 <= xx < width and mask[yy, xx] and labels[yy, xx] == 0:
                        labels[yy, xx] = label
                        queue.append((yy, xx))
        points = np.array(points)
        # Does the region touch the border of the image? If so, part of it is cut off and its area
        # is incomplete.
        touches_edge = bool(np.any((points[:, 0] == 0) | (points[:, 0] == height - 1) | (points[:, 1] == 0) | (points[:, 1] == width - 1)))
        # Record the region's label, its size in pixels, the border flag and its centre point.
        objects.append({"label": label, "area_px": len(points), "touches_edge": touches_edge,
                        "centroid_y_px": float(points[:, 0].mean()), "centroid_x_px": float(points[:, 1].mean())})
    return labels, objects


def segment(image: np.ndarray, threshold: int) -> tuple[np.ndarray, list[dict], dict]:
    """Select pixels brighter than `threshold`, group them into regions and apply the quality-control
    filters.
    Returns (cleaned label image, list of accepted regions, summary of what was found and removed).
    """
    # Pixels strictly brighter than the threshold are foreground. Label them into regions.
    labels, objects = label_components(image > threshold)
    # Quality control: count the regions dropped for being too small, and the large regions dropped
    # for touching the image border.
    small = sum(obj["area_px"] < MIN_AREA_PX for obj in objects)
    border = sum(obj["area_px"] >= MIN_AREA_PX and obj["touches_edge"] for obj in objects)
    # Keep only regions that are big enough and do not touch the border.
    accepted = [obj for obj in objects if obj["area_px"] >= MIN_AREA_PX and not obj["touches_edge"]]
    accepted_ids = [obj["label"] for obj in accepted]
    # A cleaned label image that contains only the accepted regions (everything else becomes 0, the
    # background).
    cleaned = np.where(np.isin(labels, accepted_ids), labels, 0).astype(np.uint16)
    # A summary of what happened. It is saved to results.json so every count can be checked.
    summary = {"threshold_raw_au": threshold, "foreground_pixels": int((image > threshold).sum()),
               "components_before_qc": len(objects), "small_components_excluded": small,
               "large_border_components_excluded": border, "accepted_2d_regions": len(accepted),
               "accepted_area_px": int(np.count_nonzero(cleaned))}
    return cleaned, accepted, summary


def display_gray(image: np.ndarray, limits: tuple[float, float]) -> np.ndarray:
    """Turn raw values into 0-255 grey levels for display only. Measurements always use the raw
    numbers, never this picture.
    """
    # Map the chosen intensity range [low, high] onto 0-255. Values outside the range are clipped.
    low, high = limits
    return np.uint8(np.clip((image.astype(float) - low) / (high - low), 0, 1) * 255)


def save_display(image: np.ndarray, labels: np.ndarray, path: Path, limits: tuple[float, float], scale_um_per_px: float) -> None:
    """Save a picture of the image, optionally with the region outlines in pink and a 10 micrometre
    scale bar.
    """
    gray = display_gray(image, limits)
    rgb = np.repeat(gray[:, :, None], 3, axis=2)
    if labels.any():
        # Boundary pixels are labelled pixels whose label differs from a neighbour above, below,
        # left or right.
        boundary = (labels != 0) & ((labels != np.roll(labels, 1, 0)) | (labels != np.roll(labels, -1, 0)) | (labels != np.roll(labels, 1, 1)) | (labels != np.roll(labels, -1, 1)))
        # Paint the region outlines pink so the overlay shows exactly what the mask selected.
        rgb[boundary] = (255, 110, 120)
    # Enlarge 4 times. Nearest-neighbour resizing keeps every pixel sharp, so the picture stays
    # honest.
    result = Image.fromarray(rgb).resize((1024, 1024), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(result)
    # Draw a 10 micrometre scale bar: 10 micrometres divided by micrometres-per-pixel gives pixels,
    # multiplied by 4 for the enlargement.
    scale_pixels = round(10 / scale_um_per_px * 4)
    draw.rectangle((30, 950, 30 + scale_pixels, 963), fill="white")
    font = ImageFont.truetype("/System/Library/Fonts/Avenir.ttc", 28)
    draw.rectangle((23, 908, 245, 946), fill="black")
    draw.text((30, 910), "10 micrometres", fill="white", font=font)
    result.save(path)


def sanity_checks() -> dict:
    """Three tiny tests with known answers. If any assert fails, the analysis code cannot be trusted."""
    # Test 1: an image with only two brightness values (0 and 10). Otsu must split right at the dark
    # value.
    bimodal = np.array([[0, 0, 0, 10, 10]], dtype=np.uint16)
    assert otsu_threshold(bimodal) == 0
    # Test 2: draw two 10 x 10 squares and one single pixel in the corner. Labelling must find
    # regions of 100, 100 and 1 pixels, and flag only the corner pixel as touching the border.
    geometry = np.zeros((20, 30), dtype=bool)
    geometry[2:12, 2:12] = True
    geometry[4:14, 18:28] = True
    geometry[0, 29] = True
    _, objects = label_components(geometry)
    assert sorted(obj["area_px"] for obj in objects) == [1, 100, 100]
    assert sum(obj["touches_edge"] for obj in objects) == 1
    # Test 3: unit arithmetic. 100 pixels of 0.26 x 0.26 micrometres cover 6.76 square micrometres.
    assert abs(100 * 0.26 ** 2 - 6.76) < 1e-12
    return {"known_bimodal_threshold": "pass", "known_geometry_components_and_border": "pass", "area_units": "pass"}


def main() -> None:
    """Run the whole analysis: load, check, segment, measure, stress-test and save everything."""
    # Start a timer for the run receipt.
    started = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    # STEP 1 - load the image and prove it is the file we expect.
    input_path = ROOT / "data/cells3d-with-metadata.tif"
    if sha256(input_path) != EXPECTED_SHA256:
        raise ValueError("Input image SHA-256 differs from the retained source")
    stack, metadata = load_stack(input_path)
    # Load the official, unmodified copy of the dataset and compare it pixel by pixel. The metadata
    # copy stores the two channels in the opposite order, so we check the real pixels instead of
    # trusting a remembered channel number.
    original, _ = load_stack(ROOT / "data/cells3d-original-channel-order.tif")
    assert stack.shape == original.shape == (60, 2, 256, 256)
    # The original file's documented membrane/nuclei order is reversed in the metadata copy.
    assert np.array_equal(stack[:, 0], original[:, 1])
    assert np.array_equal(stack[:, 1], original[:, 0])
    channel_verification = {"metadata_file_channel_0": "nuclei", "metadata_file_channel_1": "membranes",
                            "method": "all pixels in all 60 depths equal the corresponding reversed channel of the official documented cells3d.tif", "all_pixels_equal": True}
    # Pixel size in micrometres = 1 / (pixels per micrometre).
    pixel_size_x = 1 / metadata["x_resolution_px_per_um"]
    pixel_size_y = 1 / metadata["y_resolution_px_per_um"]
    # Preserve the metadata reciprocal, while using the official rounded 0.26 um scale for lesson arithmetic.
    assert abs(pixel_size_x - 0.26) < 1e-6 and abs(pixel_size_y - 0.26) < 1e-6
    dx_um = dy_um = 0.26
    # STEP 2 - pick the plane and the channel: depth SLICE_Z, channel 0 = nuclei.
    image = stack[SLICE_Z, 0]
    # STEP 3 - choose a threshold with Otsu's method, then turn the bright pixels into labelled
    # regions.
    baseline_threshold = otsu_threshold(image)
    labels, objects, baseline = segment(image, baseline_threshold)
    # A rough background level: the 10th percentile, meaning the value below which the darkest 10%
    # of pixels fall.
    background_proxy = float(np.percentile(image, 10))
    # STEP 4 - measure each accepted region. Area in square micrometres = pixel count x pixel width
    # x pixel height. Mean raw intensity = average detector value of the region's pixels.
    rows = []
    for obj in objects:
        mean_au = float(image[labels == obj["label"]].mean())
        rows.append({**obj, "area_um2": obj["area_px"] * dx_um * dy_um,
                     "mean_raw_intensity_au": mean_au,
                     "mean_minus_p10_background_proxy_au": mean_au - background_proxy,
                     "slice_index_zero_based": SLICE_Z, "channel_index": 0,
                     "mask_status": "algorithm-generated; no manual ground truth"})
    # STEP 5 - save the measurement table and the images. Keeping the label image lets anyone check
    # the table against the pixels that produced it.
    with (OUT / "nuclear_region_measurements.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    np.save(OUT / "nuclear_region_labels_z30.npy", labels)
    Image.fromarray(labels).save(OUT / "nuclear_region_labels_z30.tif")
    Image.fromarray(image).save(OUT / "nuclei_raw_z30.tif")
    Image.fromarray(stack[SLICE_Z, 1]).save(OUT / "membranes_raw_z30.tif")
    # Display range for the nuclei picture: from the 1st to the 99.5th percentile, so a few very
    # bright pixels do not wash out the rest.
    limits = tuple(float(x) for x in np.percentile(image, [1, 99.5]))
    save_display(image, np.zeros_like(labels), OUT / "nuclei_z30_display.png", limits, dx_um)
    save_display(image, labels, OUT / "nuclei_z30_overlay.png", limits, dx_um)
    membrane_limits = tuple(float(x) for x in np.percentile(stack[SLICE_Z, 1], [1, 99.5]))
    save_display(stack[SLICE_Z, 1], np.zeros_like(labels), OUT / "membranes_z30_display.png", membrane_limits, dx_um)
    # STEP 6 - stress test. Halve every pixel value (a mathematical change, not a new experiment)
    # and segment again, first with the old threshold, then with a re-estimated Otsu threshold.
    stress_image = (image // 2).astype(np.uint16)
    fixed_labels, _, fixed = segment(stress_image, baseline_threshold)
    adapted_threshold = otsu_threshold(stress_image)
    adapted_labels, _, adapted = segment(stress_image, adapted_threshold)
    save_display(stress_image, fixed_labels, OUT / "half_brightness_fixed_threshold_overlay.png", limits, dx_um)
    save_display(stress_image, adapted_labels, OUT / "half_brightness_otsu_overlay.png", limits, dx_um)
    # Intersection over union: the share of selected pixels that two masks have in common (1.0 means
    # identical masks).
    def iou(reference: np.ndarray, comparison: np.ndarray) -> float:
        union = np.count_nonzero((reference > 0) | (comparison > 0))
        return float(np.count_nonzero((reference > 0) & (comparison > 0)) / union) if union else 1.0
    # STEP 7 - maximum-intensity projection: for every pixel position keep the brightest value found
    # at any depth, then segment that single flattened picture. Depth information is lost, so this
    # count cannot be compared directly with the single-plane count.
    projection = stack[:, 0].max(axis=0)
    projection_labels, _, projection_result = segment(projection, otsu_threshold(projection))
    save_display(projection, projection_labels, OUT / "nuclei_max_projection_overlay.png", tuple(float(x) for x in np.percentile(projection, [1, 99.5])), dx_um)
    # A contact sheet of six depth planes, to show how the picture changes with depth.
    montage = Image.new("RGB", (3 * 512, 2 * 544), "white")
    draw = ImageDraw.Draw(montage)
    font = ImageFont.truetype("/System/Library/Fonts/Avenir.ttc", 17)
    for i, z in enumerate((10, 20, 30, 40, 50, 59)):
        view = Image.fromarray(display_gray(stack[z, 0], limits)).convert("RGB").resize((512, 512))
        x, y = (i % 3) * 512, (i // 3) * 544
        montage.paste(view, (x, y + 32))
        draw.text((x + 10, y + 4), f"Nuclei: z={z}, depth={z * 0.29:.2f} um from first plane", fill="black", font=font)
    montage.save(OUT / "depth_contact_sheet.png")
    # STEP 8 - write down everything needed to repeat and judge this analysis: axes, shapes, pixel
    # sizes, thresholds, counts and caveats.
    metadata.update({"axes": "ZCYX", "shape": list(stack.shape), "dtype": "uint16", "channel_verification": channel_verification,
                     "pixel_size_um_from_tiff": {"x": pixel_size_x, "y": pixel_size_y, "z": float(metadata["metadata"]["spacing"])},
                     "pixel_size_um_for_arithmetic": {"x": dx_um, "y": dy_um, "z": 0.29}})
    summary = {"scope": "Educational 2D threshold/measurement/QC demonstration on one real fluorescence monolayer stack; no training, no drug condition, no segmentation accuracy estimate.",
               "source_sha256": EXPECTED_SHA256, "slice_index_zero_based": SLICE_Z,
               "z_position_relative_to_first_plane_um": SLICE_Z * 0.29,
               "field_width_um": image.shape[1] * dx_um,
               "slice_spacing_um": 0.29, "interval_between_first_and_last_slice_centres_um": 59 * 0.29,
               "qc_min_area_px": MIN_AREA_PX, "qc_min_area_um2": MIN_AREA_PX * dx_um * dy_um,
               "background_proxy_p10_au": background_proxy,
               "raw_slice_min_max_au": [int(image.min()), int(image.max())],
               "dtype_max_fraction": float(np.mean(image == 65535)),
               "saturation_caveat": "Zero dtype-maximum pixels does not rule out detector clipping below 65535; acquisition settings are unavailable.",
               "baseline_otsu": baseline,
               "controlled_half_brightness_fixed_baseline_threshold": {**fixed, "binary_mask_iou_against_original_mask_not_ground_truth": iou(labels, fixed_labels)},
               "controlled_half_brightness_reestimated_otsu": {**adapted, "binary_mask_iou_against_original_mask_not_ground_truth": iou(labels, adapted_labels)},
               "max_intensity_projection_baseline": projection_result,
               "first_retained_object": rows[0],
               "mean_intensity_of_retained_pixels_au": float(image[labels > 0].mean()),
               "mean_intensity_of_identical_mask_after_halving_au": float(stress_image[labels > 0].mean()),
               "independent_specimens": 1,
               "interpretation": "Connected bright 2D regions are candidates, not established complete nuclei or cells. A slice cuts through 3D objects; thresholding can fragment or merge them. The brightness stress test changes pixels, not biology.",
               "sanity_checks": sanity_checks()}
    (OUT / "image_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (OUT / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    # STEP 9 - a run receipt with the fingerprint of every output file, the software versions and
    # the hardware, so the run can be audited later.
    outputs = [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
               for path in sorted(OUT.iterdir()) if path.is_file() and path.name != "run_receipt.json"]
    receipt = {"artifact_id": "ai-drug-discovery-2-real-monolayer-qc-v1", "producer_episode": 2,
               "utc": datetime.now(timezone.utc).isoformat(), "command": "Tools/ssd-run.sh python Playlists/ai-in-drug-discovery/2/code/microscopy_demo.py",
               "python": sys.version, "numpy": np.__version__, "pillow": pillow_version,
               "hardware": {"machine": platform.machine(), "platform": platform.platform(), "processor": platform.processor()},
               "elapsed_seconds": time.perf_counter() - started, "random_seed": "not applicable; deterministic",
               "source_script_sha256": sha256(Path(__file__)), "input_sha256": EXPECTED_SHA256,
               "ground_truth": "none for the real image; generated masks are retained as algorithm outputs",
               "model_or_checkpoint": "none", "split": "one specimen; no training/test benchmark",
               "target_or_compound_match": "none: separate imaging demonstration, not EGFR/KRAS treatment evidence",
               "units": {"spatial": "micrometres", "area": "square micrometres", "intensity": "raw arbitrary detector units"},
               "source_rights": "CC0 per current official scikit-image data README; Allen Institute for Cell Science",
               "outputs": outputs}
    (OUT / "run_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


# Run main() only when the file is executed directly, not when it is imported.
if __name__ == "__main__":
    main()
