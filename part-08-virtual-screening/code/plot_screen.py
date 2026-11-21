"""Draw the three figures of Part 8 from the executed screen: the comparison bars, the two distance heat maps and the first three structures.

What this file does
    * comparison draws bars for the mean and the closest pair distance of the score-only list and the Butina + MaxMin list.
    * heatmaps draws the 20 x 20 distance table of each shortlist on one shared colour scale.
    * structures draws the first three MaxMin choices as 2D molecule pictures.

What it needs
    Python 3.10 or newer, Pillow and RDKit, plus SCREEN_REPORT.json and CANDIDATE_SCORES.json from screen_library.py.
    The text uses a TrueType font; change FONT below to any font file on your computer.

Run
    python code/plot_screen.py data/output data/plots

What to expect
    Three PNG files: shortlist-comparison.png, shortlist-heatmaps.png and first-three-structures.png.
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rdkit import Chem
from rdkit.Chem import Draw

from selection import distance_matrix

# Colours: dark green-blue text, and one bar colour for each shortlist.
INK = "#233c39"
COLOURS = ("#37789c", "#2c8d70")
# Any TrueType font file works; this name is found in the standard font folders of most systems.
FONT = Path("DejaVuSans.ttf")


def panel() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Make a blank white picture and the pen that draws on it."""
    picture = Image.new("RGB", (1480, 820), "#fff")
    return picture, ImageDraw.Draw(picture)


def label(draw: ImageDraw.ImageDraw, position: tuple, text: str, size: int, anchor="lt", fill=INK) -> None:
    """Write text at a position; the anchor says which corner or edge of the text sits at that position."""
    draw.text(position, text, font=ImageFont.truetype(str(FONT), size), fill=fill, anchor=anchor)


def comparison(report: dict, output: Path) -> None:
    """Draw the two bar groups that compare the shortlists."""
    image, draw = panel()
    label(draw, (740, 38), "Two shortlists, twenty candidates each", 56, "mt")
    label(draw, (740, 105), "Distance range 0 to 1 · higher values indicate less fingerprint overlap", 29, "mt")
    rows = (("Mean pair distance", "mean_pairwise_distance"), ("Closest pair distance", "smallest_pairwise_distance"))
    for group, (title, metric) in enumerate(rows):
        y = 215 + group * 265
        label(draw, (60, y), title, 41)
        for index, (key, title) in enumerate((("score_only", "Score only"), ("maxmin", "Butina + MaxMin"))):
            val = report[key][metric]
            top = y + 60 + index * 75
            label(draw, (62, top + 15), title, 32)
            # A pale track shows the full 0-to-1 range; the coloured bar is as long as the distance value.
            draw.rounded_rectangle((390, top, 1320, top + 56), radius=13, fill="#eef4f4")
            end = 390 + val * 930
            draw.rounded_rectangle((390, top, end, top + 56), radius=13, fill=COLOURS[index])
            label(draw, (end + 19, top + 29), f"{val:.3f}", 33, "lm")
    label(draw, (740, 761), "20 virtual analogue proposals in each list · no assayed potency values", 28, "mt")
    image.save(output)


def heatmaps(report: dict, candidates: dict, output: Path) -> None:
    """Draw one 20 x 20 distance table for each shortlist, shaded from pale (close) to green (far)."""
    image, draw = panel()
    label(draw, (740, 40), "The same distance scale for both shortlists", 54, "mt")
    low, high = (249, 248, 250), (39, 115, 94)
    for section, (key, title) in enumerate((("score_only", "Score only"), ("maxmin", "Butina + MaxMin"))):
        selected = report[key]["compound_ids"]
        values = distance_matrix([candidates[molecule]["morgan_on_bits"] for molecule in selected])
        x, span = 165 + 750 * section, 24
        label(draw, (x + span * 10, 120), title, 39, "mt")
        for row, line in enumerate(values):
            for column, distance in enumerate(line):
                # Blend the two end colours in proportion to the distance, so 0 is pale and 1 is dark green.
                color = tuple(round(a + (b - a) * distance) for a, b in zip(low, high))
                pos_x, pos_y = x + span * column, 178 + span * row
                draw.rectangle((pos_x, pos_y, pos_x + span - 1, pos_y + span - 1), fill=color)
        draw.rectangle((x, 178, x + 20 * span, 178 + 20 * span), outline="#486b65")
        label(draw, (x + span * 10, 675), "Rows and columns are selected compounds", 24, "mt")
    # The colour key: a small gradient strip labelled 0 on the left and 1 on the right.
    for step in range(200):
        color = tuple(round(a + (b - a) * step / 199) for a, b in zip(low, high))
        draw.rectangle((640 + step, 746, 641 + step, 766), fill=color)
    label(draw, (627, 757), "0", 28, "rm")
    label(draw, (851, 757), "1", 28, "lm")
    image.save(output)


def structures(report: dict, candidates: dict, output: Path) -> None:
    """Draw the first three MaxMin choices side by side with RDKit's grid drawing."""
    ids = report["maxmin"]["compound_ids"][:3]
    mols = [Chem.MolFromSmiles(candidates[key]["smiles"]) for key in ids]
    legends = [f"Choice {rank}  {key}" for rank, key in enumerate(ids, 1)]
    image = Draw.MolsToGridImage(mols, molsPerRow=3, subImgSize=(490, 470), legends=legends)
    image.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screen_output", type=Path)
    parser.add_argument("pictures", type=Path)
    args = parser.parse_args()
    report = json.loads((args.screen_output / "SCREEN_REPORT.json").read_text())
    scoring = json.loads((args.screen_output / "CANDIDATE_SCORES.json").read_text())
    # Look candidates up by compound ID so the shortlist IDs can be turned into fingerprints and structures.
    candidates = {row["compound_id"]: row for row in scoring["candidates"]}
    args.pictures.mkdir(parents=True, exist_ok=True)
    comparison(report, args.pictures / "shortlist-comparison.png")
    heatmaps(report, candidates, args.pictures / "shortlist-heatmaps.png")
    structures(report, candidates, args.pictures / "first-three-structures.png")
