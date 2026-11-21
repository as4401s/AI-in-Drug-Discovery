"""Draw the parity plots (predicted pIC50 against measured pIC50) from the saved test predictions.

What this file does
    For each model it draws two square panels: the random-identity test set and the held-out-scaffold test set.
    Every dot is one test molecule. A dot on the diagonal line was predicted exactly; the distance from the line is the error.

What it needs
    Python 3.10 or newer and Pillow, plus the evaluation JSON written by train_models.py and any TrueType font file.

Run
    python code/plot_results.py data/trained/egfr_evaluation.json data/plots --font DejaVuSans.ttf
    (use --font to name any TrueType font installed on your computer)

What to expect
    Five PNG files named egfr-parity-<model>.png in the output folder.
"""

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def plot(data: dict, model: str, output: Path, font_file: Path) -> None:
    """Draw one parity figure for one model and save it as a PNG.

    data: the loaded evaluation JSON. model: one of ensemble, random_forest, xgboost, mlp, gnn.
    """
    # A white canvas, then three font sizes for the title, the axis labels and the tick numbers.
    image = Image.new("RGB", (1500, 790), "#ffffff")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(font_file), 38)
    label = ImageFont.truetype(str(font_file), 26)
    tick = ImageFont.truetype(str(font_file), 22)
    ink, grid = "#24344b", "#e1e7ef"
    names = {"ensemble": "Three-model ensemble", "random_forest": "Random Forest", "xgboost": "XGBoost",
             "mlp": "Multilayer perceptron", "gnn": "Molecular graph baseline"}
    draw.text((750, 34), names[model], font=title, fill=ink, anchor="mt")
    # Use one shared axis range for both panels so they can be compared directly.
    rows = [row for split in data["splits"].values() for row in split["test_predictions"]]
    all_values = [value for row in rows for value in (row["observed_pic50"], row["predicted_pic50"][model])]
    lower, upper = math.floor(min(all_values)), math.ceil(max(all_values))
    if lower == upper:
        upper += 1
    for pane, (scheme, split) in enumerate(data["splits"].items()):
        # Each panel is a 530-pixel square placed side by side.
        x, y, size = 120 + pane * 720, 149, 530
        draw.text((x + size / 2, 88), {"random": "Random identities", "scaffold": "Held-out scaffolds"}[scheme],
                  font=label, fill=ink, anchor="mt")
        draw.text((x + size / 2, 122), f"{len(split['test_predictions'])} test compounds", font=tick,
                  fill="#526783", anchor="mt")
        draw.rectangle((x, y, x + size, y + size), fill="#f3f8fd", outline="#91a1b7", width=2)

        def position(value: float) -> float:
            """Convert a pIC50 value into a distance in pixels from the panel's lower-left corner."""
            return (value - lower) / (upper - lower) * size

        # Grid lines and tick numbers at every whole pIC50 value.
        for value in range(lower, upper + 1):
            shift = position(value)
            draw.line((x + shift, y, x + shift, y + size), fill=grid, width=2)
            draw.line((x, y + size - shift, x + size, y + size - shift), fill=grid, width=2)
            draw.text((x + shift, y + size + 13), str(value), font=tick, fill=ink, anchor="mt")
            draw.text((x - 12, y + size - shift), str(value), font=tick, fill=ink, anchor="rm")
        # The diagonal is the line of perfect prediction (predicted = measured).
        draw.line((x, y + size, x + size, y), fill="#68809d", width=3)
        # One dot per test molecule: measured value across, predicted value up.
        for row in split["test_predictions"]:
            px = x + position(row["observed_pic50"])
            py = y + size - position(row["predicted_pic50"][model])
            draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill="#427e94" if pane == 0 else "#5c5d9b",
                         outline="#ffffff", width=2)
        draw.text((x + size / 2, 738), "Measured pIC50", font=label, fill=ink, anchor="mt")
        # The vertical axis label is drawn sideways on a small transparent image and pasted in.
        y_axis = Image.new("RGBA", (280, 44), (255, 255, 255, 0))
        ImageDraw.Draw(y_axis).text((140, 22), "Predicted pIC50", font=label, fill=ink, anchor="mm")
        vertical = y_axis.rotate(90, expand=True)
        image.paste(vertical, (x - 91, y + (size - vertical.height) // 2), vertical)
    image.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation", type=Path)
    parser.add_argument("output", type=Path)
    # Any TrueType font file works; the name below is found in the standard font folders of most systems.
    parser.add_argument("--font", type=Path, default=Path("DejaVuSans.ttf"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = json.loads(args.evaluation.read_text())
    for name in ("ensemble", "random_forest", "xgboost", "mlp", "gnn"):
        plot(result, name, args.output / f"egfr-parity-{name}.png", args.font)
