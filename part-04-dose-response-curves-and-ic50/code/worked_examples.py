#!/usr/bin/env python3
"""worked_examples.py - the small calculations from Part 4 of the video, reproduced step by step.

What it does
    The video builds each hard idea from an everyday picture and a tiny example with numbers you can repeat on a
    calculator. This script runs the same examples in the same order, so you can check every number and then
    change the inputs. The last section compares a few of the numbers with the real functions of
    `dose_response_lab.py`.

      Part 1 - make a response measurement
        1.  Percent inhibition:   a bakery line makes 100 rolls a minute, then 60
        2.  Concentration:        five spoonfuls of syrup in one litre and in five litres
        3.  Units:                a staircase of thousands, 0.25 uM = 250 nM, 4,000 nM = 4 uM, 10 nM against 1 uM
        4.  Dilution:             tenfold and threefold series, and the nine lesson concentrations
        5.  Controls:             start line 1,000, finish line 100, the normalization recipe and seven readings
        6.  Replicates:           three wells (48, 52, 50) against three days (50, 38, 61)
      Part 2 - read the curve
        7.  Three points:         1, 10 and 100 nM on a curve with a midpoint of 10 nM
        8.  The logarithm:        why a ruler of concentrations uses equal steps for equal ratios
        9.  The Hill formula:     six small steps, bottom 0, top 100, midpoint 10 nM, slope 2, tested 20 nM
        10. The slope:            the same midpoint with slopes 1, 2 and 4
        11. Relative and absolute: the middle of the curve and the 50 % crossing
        12. Potency and efficacy: compound A (5 nM, 40 %) and compound B (50 nM, 95 %) at three concentrations
        13. Cheng-Prusoff:        IC50 = Ki x (1 + S / Km) for three substrate levels
        14. pIC50:                molar, log10, flip the sign
      Part 3 - fit and check in Python
        15. The practice plate:   percent to signal, three wells at nine concentrations
        16. The error:            residuals, squares, the mean and the root, against a flat baseline
        17. The search:           a coarse scan, a fine scan and the size of the real grid
        18. Residual patterns:    noise against a smooth run
        19. The bootstrap:        a hat with three slips, drawn with replacement
        20. Bracketing:           when the data cross 50 % and when they stop short
        21. Growth rate:          one drug, two cell lines, two percentages, one GR value
      Part 4 - curate potency data we can trust
        22. Six invented rows:    the decision for each row
        23. Bounds:               a reading stuck at the top of the ruler, in molar and on the pIC50 scale
        24. Assay groups:         an enzyme value and a cell value each keep their own group
        25. The exercises:        the three answers
      Against the real code
        26. The same numbers from `dose_response_lab.py` (needs NumPy; skipped when NumPy is missing)

What it needs
    Python 3.10 or newer and the standard library only for examples 1 to 25. Example 26 also needs NumPy and
    runs the functions of `dose_response_lab.py` in this folder, so run the script from the part folder.
    Every number is computed on your machine.

What to expect
    The numbers printed below match the video (rounded):
      percent inhibition 40 %                       0.25 uM = 250 nM, 4,000 nM = 4 uM, 10 nM is 100 times lower than 1 uM
      threefold series 1000, 333.3, 111.1, 37.0, 12.3     readings 820, 550, 280, 1040, 80 -> 20, 50, 80, -4.4, 102.2 %
      three wells: mean 50, spread 2            three days: mean 49.67, spread 11.5
      1, 10, 100 nM -> 9 %, 50 %, 91 %          Hill example: 20 nM -> 80 %
      slope table at 5 nM: 33.33, 20, 5.88      at 20 nM: 66.67, 80, 94.12
      absolute crossing at 200 nM               A: 20.00, 36.36, 38.10 %   B: 8.64, 47.50, 63.33 % (5, 50, 100 nM)
      Ki 10 nM -> IC50 20, 50, 100 nM
      pIC50 6, 7, 8, 9 and 8.52, 7.30, 6.60     RMSE 2.16 against a flat baseline of 33.14
      best midpoint on the fine scan 10 nM, error 2.15     bootstrap draws 49.33, 50.67, 50.67, 50
      GR value 0.414 for both cell lines        IC50 > 10,000 nM becomes pIC50 < 5
      average of 50 nM and 200 nM is 125 nM     exercise answers: pIC50 7 | 20 % | one row kept
      practice plate (example 26): IC50 about 9.78 nM, pIC50 about 8.01, RMSE 0.45, bootstrap 9.32 to 10.27 nM

Run it:
    python code/worked_examples.py
"""
import math
import random
import statistics
import sys
from pathlib import Path


def heading(text):
    """Print a section heading so the output is easy to scan."""
    print()
    print("=" * 78)
    print(text)
    print("=" * 78)


def pct(value):
    """Format a percentage with two decimals."""
    return f"{value:.2f} %"


# ---------------------------------------------------------------------------------------------
# Small functions that the examples share. They follow the same formulas as dose_response_lab.py.
# ---------------------------------------------------------------------------------------------
def hill(concentration, midpoint, slope, bottom=0.0, top=100.0):
    """Hill curve: bottom + (top - bottom) / (1 + (midpoint / concentration) ** slope)."""
    return bottom + (top - bottom) / (1 + (midpoint / concentration) ** slope)


def normalize(signal, vehicle, inhibited):
    """Percent inhibition for an assay where a LOWER signal means MORE inhibition."""
    return 100 * (vehicle - signal) / (vehicle - inhibited)


def pic50(value, unit="nM"):
    """pIC50 = -log10(IC50 in molar)."""
    to_molar = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "nM": 1e-9, "pM": 1e-12}
    return -math.log10(value * to_molar[unit])


def absolute_crossing(midpoint, slope, bottom, top, response=50.0):
    """Concentration where the curve reaches `response` percent, or None when the plateaus stop short of it."""
    if not bottom < response < top:
        return None
    return midpoint * ((response - bottom) / (top - response)) ** (1 / slope)


def rmse(observed, predicted):
    """Root of the mean of the squared differences."""
    return math.sqrt(sum((o - p) ** 2 for o, p in zip(observed, predicted)) / len(observed))


# ---------------------------------------------------------------------------------------------
# Part 1 - make a response measurement
# ---------------------------------------------------------------------------------------------
def example_1_percent_inhibition():
    heading("1. Percent inhibition: a bakery line")
    clear, blocked = 100, 60
    drop = clear - blocked
    print(f"clear aisle {clear} rolls a minute, with people in the aisle {blocked} rolls a minute")
    print(f"the output fell by {drop} rolls, which is {drop} / {clear} = {100 * drop / clear:.0f} % of the original")
    print("that share of the lost output is the percent inhibition")


def example_2_concentration():
    heading("2. Concentration: syrup in water")
    print(f"five spoonfuls in 1 litre  -> {5 / 1:.0f} spoonfuls per litre")
    print(f"five spoonfuls in 5 litres -> {5 / 5:.0f} spoonful per litre (same amount, weaker drink)")
    print("the same compound in half the liquid: concentration x", 1 / 0.5)


def example_3_units():
    heading("3. Units: a staircase of thousands")
    steps = [("molar", "M", 1), ("millimolar", "mM", 1e-3), ("micromolar", "uM", 1e-6), ("nanomolar", "nM", 1e-9)]
    for name, abbreviation, factor in steps:
        print(f"  1 {name:<11} ({abbreviation:>2}) = {factor:g} M")
    print(f"1 uM = {1000:,} nM and 1 mM = {1_000_000:,} nM  (each step down multiplies the number by 1,000)")
    print(f"0.25 uM x 1,000 = {0.25 * 1000:g} nM  (going down the stairs multiplies the number)")
    print(f"4,000 nM / 1,000 = {4000 / 1000:g} uM  (going up the stairs divides the number)")
    ten_nm, one_um = 10, 1 * 1000
    print(f"10 nM against 1 uM: write 1 uM as {one_um} nM first -> {one_um / ten_nm:.0f} times lower")


def example_4_dilution():
    heading("4. Dilution: glasses of squash and the lesson series")
    tenfold = [1000 / 10 ** k for k in range(4)]
    print("tenfold series  :", " -> ".join(f"{v:g}" for v in tenfold))
    threefold = [1000 / 3 ** k for k in range(5)]
    print("threefold series:", " -> ".join(f"{v:.1f}" for v in threefold))
    lesson = [0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000]
    ratios = [b / a for a, b in zip(lesson, lesson[1:])]
    print(f"the lesson series has {len(lesson)} concentrations from {lesson[0]} to {lesson[-1]} nM")
    print("steps between neighbours:", ", ".join(f"{r:.2f}" for r in ratios), "(about 3-fold, equal ratios)")


def example_5_controls():
    heading("5. Controls: start line and finish line")
    vehicle, inhibited = 1000, 100
    distance = vehicle - inhibited
    print(f"vehicle (start line, 0 % inhibition)   : {vehicle}")
    print(f"inhibited reference (finish line, 100 %): {inhibited}")
    print(f"distance between the lines: {vehicle} - {inhibited} = {distance} units")
    reading = 550
    print(f"a test well at {reading} is {vehicle - reading} units from the start line")
    print(f"percent inhibition = 100 x {vehicle - reading} / {distance} = {normalize(reading, vehicle, inhibited):.0f} %")
    print("the normalization recipe, three steps: subtract from the vehicle, divide by the distance, multiply by 100")
    first = 820
    print(f"  reading {first}: {vehicle} - {first} = {vehicle - first}; {vehicle - first} / {distance} = {(vehicle - first) / distance:g}; x 100 = {normalize(first, vehicle, inhibited):.0f} %")
    for reading in (1000, 550, 280, 100, 1040, 80):
        print(f"  reading {reading:>4} -> {normalize(reading, vehicle, inhibited):6.1f} % inhibition")
    print("values outside 0 to 100 stay exactly as they come, because they carry real information about noise")


def example_6_replicates():
    heading("6. Replicates: photos of one cake against three cakes")
    wells = [48, 52, 50]
    days = [50, 38, 61]
    for name, values in (("three wells, one preparation", wells), ("three days, independent preparations", days)):
        print(f"{name}: values {values}  mean {statistics.mean(values):.2f}  spread (standard deviation) {statistics.stdev(values):.2f}")
    print("the day-to-day spread is the bigger story")
    print("our synthetic plate: 3 technical wells x 9 concentrations =", 3 * 9, "wells")


# ---------------------------------------------------------------------------------------------
# Part 2 - read the curve
# ---------------------------------------------------------------------------------------------
def example_7_three_points():
    heading("7. Three points on the curve (midpoint 10 nM, slope 1)")
    for concentration in (1, 10, 100):
        print(f"  {concentration:>4} nM -> {hill(concentration, 10, 1):5.1f} %")


def example_8_logarithm():
    heading("8. The logarithm and the ruler of concentrations")
    marks = [1, 10, 100, 1000]
    print("regular ruler, position as a share of the full length:")
    print("   ", [f"{m / 1000:g}" for m in marks])
    print("log ruler, position = log10(c) / 3:")
    print("   ", [f"{math.log10(m) / 3:.3f}" for m in marks], " log10 values:", [round(math.log10(m)) for m in marks])
    print("each tenfold step gets the same room; log10 of zero is undefined, so the zero control is plotted separately")


def example_9_hill_formula():
    heading("9. The Hill formula in six small steps")
    bottom, top, midpoint, slope, tested = 0, 100, 10, 2, 20
    s1 = midpoint / tested
    s2 = s1 ** slope
    s3 = s2 + 1
    s4 = 1 / s3
    s5 = s4 * (top - bottom)
    s6 = s5 + bottom
    print(f"settings: bottom {bottom}, top {top}, midpoint {midpoint} nM, slope {slope}, tested {tested} nM")
    print(f"step 1: {midpoint} / {tested} = {s1}")
    print(f"step 2: {s1} ^ {slope} = {s2}")
    print(f"step 3: {s2} + 1 = {s3}")
    print(f"step 4: 1 / {s3} = {s4}")
    print(f"step 5: {s4} x {top - bottom} = {s5}")
    print(f"step 6: {s5} + {bottom} = {s6}  -> {s6:.0f} % inhibition at {tested} nM")
    print(f"check with hill(): {hill(tested, midpoint, slope):.0f} %")


def example_10_slope():
    heading("10. The slope: same midpoint, three slopes")
    print("midpoint 10 nM, so every slope gives 50 % at 10 nM")
    print(f"{'slope':>6} {'at 5 nM':>10} {'at 10 nM':>10} {'at 20 nM':>10}")
    for slope in (1, 2, 4):
        print(f"{slope:>6} {hill(5, 10, slope):9.2f}% {hill(10, 10, slope):9.2f}% {hill(20, 10, slope):9.2f}%")


def example_11_relative_and_absolute():
    heading("11. Relative midpoint and absolute 50 % crossing")
    print("compound with plateaus 0 and 40, midpoint 10 nM")
    print(f"  response at the midpoint: {hill(10, 10, 1, 0, 40):.0f} %   (half of its own best level)")
    print(f"  absolute 50 % crossing  : {absolute_crossing(10, 1, 0, 40)}   (the curve stays below 50 %)")
    bottom, top, midpoint = 10, 70, 100
    print(f"second example: bottom {bottom}, top {top}, midpoint {midpoint} nM, slope 1")
    print(f"  middle of {bottom} and {top} is {(bottom + top) / 2:.0f} %, and the curve gives {hill(midpoint, midpoint, 1, bottom, top):.0f} % at the midpoint")
    print(f"  absolute 50 % crossing at {absolute_crossing(midpoint, 1, bottom, top):.0f} nM")


def example_12_potency_and_efficacy():
    heading("12. Potency and efficacy")
    compounds = {"A": (5, 40), "B": (50, 95)}
    for name, (ic50, maximum) in compounds.items():
        reaches = "reaches" if maximum > 50 else "stays below"
        print(f"compound {name}: IC50 {ic50} nM, maximum effect {maximum} %  ({reaches} 50 % inhibition)")
    print("response of each compound at three concentrations (slope 1):")
    print(f"{'nM':>6} {'A':>8} {'B':>8}")
    for concentration in (5, 50, 100):
        a = hill(concentration, 5, 1, 0, 40)
        b = hill(concentration, 50, 1, 0, 95)
        print(f"{concentration:>6} {a:7.2f}% {b:7.2f}%")
    print("the lower IC50 belongs to A; B reaches far more inhibition: two different questions, two pieces of evidence")


def example_13_cheng_prusoff():
    heading("13. Cheng-Prusoff: IC50 = Ki x (1 + S / Km)")
    ki = 10
    for label, ratio in (("S = Km", 1), ("S = 4 Km", 4), ("S = 9 Km", 9)):
        print(f"  Ki {ki} nM, {label:<8} -> IC50 = {ki} x (1 + {ratio}) = {ki * (1 + ratio)} nM")
    print("one compound, one grip (Ki), three IC50 values: the conditions changed, so record them beside the value")


def example_14_pic50():
    heading("14. pIC50: molar, log10, flip the sign")
    for value, unit in ((1, "uM"), (100, "nM"), (10, "nM"), (1, "nM")):
        print(f"  {value:>3} {unit}: pIC50 = {pic50(value, unit):.0f}")
    print("in-between values with the same recipe:")
    for value in (3, 50, 250, 2.6):
        print(f"  {value:>5} nM: pIC50 = {pic50(value):.3f}")


# ---------------------------------------------------------------------------------------------
# Part 3 - fit and check in Python
# ---------------------------------------------------------------------------------------------
def example_15_practice_plate():
    heading("15. The practice plate: percent to signal and back")
    vehicle, inhibited = 1000, 100
    doses = [0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000]
    print(f"known truth: midpoint 10 nM, slope 1, plateaus 0 and 100; 0 % = {vehicle} units, 100 % = {inhibited} units")
    print(f"{'nM':>7} {'model %':>9} {'signal':>9}")
    for dose in doses:
        percent = hill(dose, 10, 1)
        signal = vehicle - percent / 100 * (vehicle - inhibited)
        print(f"{dose:>7g} {percent:>8.2f}% {signal:>9.1f}")
    print(f"at the midpoint the model gives exactly {hill(10, 10, 1):.0f} %")
    print(f"3 wells x {len(doses)} concentrations = {3 * len(doses)} test wells; a fixed seed gives every learner the same wiggle")


def example_16_error():
    heading("16. The error: residuals, squares, mean, root")
    observed, predicted = [12, 49, 93], [9, 50, 91]
    differences = [o - p for o, p in zip(observed, predicted)]
    squares = [d * d for d in differences]
    mean_square = sum(squares) / len(squares)
    print(f"observed {observed}, predicted {predicted}")
    print("differences (residuals):", [f"{d:+d}" for d in differences])
    print("squares                :", squares)
    print(f"average of the squares : {sum(squares)} / {len(squares)} = {mean_square:.2f}")
    print(f"root                   : sqrt({mean_square:.2f}) = {math.sqrt(mean_square):.2f} percentage points (the RMSE)")
    baseline = [50, 50, 50]
    base_differences = [o - p for o, p in zip(observed, baseline)]
    base_squares = [d * d for d in base_differences]
    print("a flat baseline that predicts 50 everywhere:")
    print("  differences:", [f"{d:+d}" for d in base_differences], " squares:", base_squares)
    print(f"  average {sum(base_squares) / 3:.0f}, root {rmse(observed, baseline):.2f}")
    print(f"the comparison: {rmse(observed, predicted):.2f} against {rmse(observed, baseline):.2f}: a good fit shows a wide gap")


def example_17_search():
    heading("17. The search: coarse first, then finer")
    doses, observed = [1, 10, 100], [12, 49, 93]

    def error(midpoint):
        return rmse(observed, [hill(d, midpoint, 1) for d in doses])

    print("coarse scan, slope 1:")
    for midpoint in (1, 3, 10, 30, 100):
        print(f"  midpoint {midpoint:>4} nM -> error {error(midpoint):6.2f}")
    fine = [7, 8, 9, 10, 11, 12, 14]
    print("zoom in around 10 nM (the same list as the video):")
    for midpoint in fine:
        print(f"  midpoint {midpoint:>4} nM -> error {error(midpoint):6.2f}")
    best = min(fine, key=error)
    print(f"the lowest is still {best} nM, with error {error(best):.2f}")
    finer = [9 + 0.05 * k for k in range(41)]
    finest = min(finer, key=error)
    print(f"extra: a still finer scan in steps of 0.05 nM puts the lowest at {finest:.2f} nM, error {error(finest):.2f}")
    print(f"the real fit_hill() scores {41} x {41} = {41 * 41} midpoint and slope pairs, keeps the best cell,")
    print("shrinks the box around it and repeats for eight rounds")


def example_18_residual_patterns():
    heading("18. Residual patterns: noise against a smooth run")
    noise = [3, -1, 2, -2, 1]
    run = [6, 4, 1, -3, -7]

    def changes(values):
        return sum(1 for a, b in zip(values, values[1:]) if (a > 0) != (b > 0))

    print(f"noise : {[f'{v:+d}' for v in noise]}  sign changes {changes(noise)}, largest size {max(abs(v) for v in noise)}")
    print(f"a run : {[f'{v:+d}' for v in run]}  sign changes {changes(run)} (one smooth run from positive to negative)")
    print("a single small error number can hide a pattern like this one: look at the residuals against concentration")


def example_19_bootstrap():
    heading("19. The bootstrap: a hat with three slips")
    slips = [48, 52, 50]
    draws = [[48, 48, 52], [52, 50, 50], [48, 52, 52], [50, 50, 50]]
    for number, draw in enumerate(draws, start=1):
        print(f"  draw {number}: {draw} -> mean {statistics.mean(draw):.2f}")
    print("draw, record, put the slip back, draw again: the same slip can appear twice")
    rng = random.Random(20261114)
    means = sorted(statistics.mean(rng.choices(slips, k=3)) for _ in range(400))
    print(f"400 redraws of the three slips: the means wander between {means[0]:.2f} and {means[-1]:.2f}")
    print("the spread of the redrawn means shows how far the wells could shift the answer")
    print("the real bootstrap() redraws wells, recalculates the means and refits 400 times (see example 26)")


def example_20_bracketing():
    heading("20. Bracketing: when does the curve cross 50 %?")
    short = [5, 14, 27, 35, 38]
    print(f"five means {short}: the top response is {max(short)} %, so the data stop short of 50 %")
    print("honest report: IC50 is greater than the highest tested concentration (a bound)")
    bracketed = [22, 41, 63]
    below = max(v for v in bracketed if v < 50)
    above = min(v for v in bracketed if v > 50)
    print(f"three means {bracketed}: 50 % lies between {below} % (second mean) and {above} % (third mean), so a crossing can be estimated")
    print("fit_hill() checks this first; otherwise it returns status refused, with the direction of the bound")


def example_21_growth_rate():
    heading("21. Growth rate: one drug, two cell lines")
    start = 1000
    fast_untreated, slow_untreated = 4000, 2000
    fast_doublings, slow_doublings = math.log2(fast_untreated / start), math.log2(slow_untreated / start)
    print(f"fast line: {start} -> {fast_untreated} untreated = {fast_doublings:.0f} doublings; slow line: {start} -> {slow_untreated} = {slow_doublings:.0f} doubling")
    fast_treated = start * 2 ** (fast_doublings / 2)
    slow_treated = start * 2 ** (slow_doublings / 2)
    print(f"a drug that halves the growth rate: fast line {fast_treated:,.0f} cells, slow line {slow_treated:,.0f} cells")
    print(f"viability = treated / untreated: fast {fast_treated / fast_untreated:.1%}, slow {slow_treated / slow_untreated:.1%} (two percentages)")
    gr_fast = 2 ** (math.log2(fast_treated / start) / fast_doublings) - 1
    gr_slow = 2 ** (math.log2(slow_treated / start) / slow_doublings) - 1
    print(f"GR value = 2 ^ (1/2) - 1 = {gr_fast:.3f} for the fast line and {gr_slow:.3f} for the slow line")
    print("1 means growth like untreated, 0 means growth has stopped, below 0 means cells are dying (a preview; read the paper)")


# ---------------------------------------------------------------------------------------------
# Part 4 - curate potency data we can trust
# ---------------------------------------------------------------------------------------------
def classify_teaching_row(row):
    """A tiny teaching version of classify(): returns (shelf, reason) for one invented row."""
    if row.get("flag") == "possible_duplicate":
        return "excluded", "duplicate flag (one measurement counted twice)"
    if row["endpoint"] != "IC50":
        return f"{row['endpoint']} shelf", "a different endpoint"
    if row["assay"] == "cell":
        return "cell shelf", "a cell assay measures something different from an enzyme assay"
    if row["relation"] != "=":
        return "bound shelf", "relation kept: the value is a range"
    to_nm = {"nM": 1, "uM": 1000}[row["unit"]]
    value_nm = row["value"] * to_nm
    note = "unit converted" if row["unit"] != "nM" else "exact value"
    return "exact-value shelf", f"{note}: {value_nm:g} nM"


def example_22_invented_rows():
    heading("22. Six invented rows and their decisions")
    rows = [
        {"endpoint": "IC50", "relation": "=", "value": 12, "unit": "nM", "assay": "enzyme"},
        {"endpoint": "IC50", "relation": ">", "value": 10000, "unit": "nM", "assay": "enzyme"},
        {"endpoint": "IC50", "relation": "=", "value": 3, "unit": "uM", "assay": "enzyme"},
        {"endpoint": "IC50", "relation": "=", "value": 85, "unit": "nM", "assay": "cell"},
        {"endpoint": "Ki", "relation": "=", "value": 8, "unit": "nM", "assay": "enzyme"},
        {"endpoint": "IC50", "relation": "=", "value": 40, "unit": "nM", "assay": "enzyme", "flag": "possible_duplicate"},
    ]
    print("rows are invented for teaching; the real rules live in classify() of curate_activities.py")
    for row in rows:
        shelf, reason = classify_teaching_row(row)
        print(f"  {row['endpoint']:<4}{row['relation']} {row['value']:>6g} {row['unit']:<2} {row['assay']:<6} -> {shelf:<18} ({reason})")


def example_23_bounds():
    heading("23. Bounds: a reading stuck at the top of the ruler")
    print("a scale that stops at 150 kg shows 150 for every suitcase of 150 kg or more: the real weight is 150 or more")
    top_nm = 10000
    top_molar = top_nm * 1e-9
    print(f"IC50 > {top_nm:,} nM  ->  IC50 > {top_molar:g} M   (unit first, scale second; 'greater than' stays attached)")
    print(f"pIC50 = -log10({top_molar:g}) = {-math.log10(top_molar):.0f}, and a larger concentration gives a smaller pIC50, so pIC50 < 5")
    print("the bound describes a whole range; three IC50 values that all satisfy 'greater than 10,000 nM':")
    for value in (12000, 50000, 1000000):
        print(f"  IC50 {value:>9,} nM -> pIC50 {pic50(value):.2f}")
    print("bounds keep their relation in their own group; a missing value stays missing and an unknown concentration stays unknown")


def example_24_assay_groups():
    heading("24. Assay groups: a number with a unit can hide a different experiment")
    values = {"enzyme assay": 50, "cell assay": 200}
    for name, value in values.items():
        print(f"  {name}: {value} nM")
    print(f"the average {statistics.mean(values.values()):g} nM mixes two experiments; each group keeps its own count, values and sources")
    print("an open record stays open and labeled; the next step is to read the original assay descriptions")


def example_25_exercises():
    heading("25. The three exercises")
    print(f"exercise 1: 100 nM = 100 x 1e-9 M = 1e-7 M, log10(1e-7) = -7, pIC50 = {pic50(100):.0f}")
    print(f"exercise 2: plateaus 0 and 40, midpoint 10 nM: the midpoint response is {hill(10, 10, 1, 0, 40):.0f} %")
    crossing = absolute_crossing(10, 1, 0, 40)
    print(f"            the curve stays below 50 %, so the absolute crossing is {crossing}: the best report is a bound")
    print("exercise 3: one eligible row and one excluded row: read unit, relation, assay and source for each row")
    print("            then check the arithmetic, and then check the meaning")


# ---------------------------------------------------------------------------------------------
# Against the real code
# ---------------------------------------------------------------------------------------------
def example_26_real_code():
    heading("26. The same numbers from dose_response_lab.py")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import numpy  # noqa: F401  (needed by the lab module)
        import dose_response_lab as lab
    except ImportError as error:
        print(f"skipped: {error}. Install NumPy (pip install numpy) and run the script from the part folder.")
        return
    checks = [
        ("hill(20, 10, 2)", float(lab.hill(20, 10, 2)), hill(20, 10, 2)),
        ("hill(5, 10, 4)", float(lab.hill(5, 10, 4)), hill(5, 10, 4)),
        ("normalize(550, 1000, 100)", float(lab.normalize(550, 1000, 100)), normalize(550, 1000, 100)),
        ("pic50(50, 'nM')", lab.pic50(50, "nM"), pic50(50)),
        ("absolute_crossing(100, 1, 10, 70)", lab.absolute_crossing(100, 1, 10, 70), absolute_crossing(100, 1, 10, 70)),
    ]
    for name, real, teaching in checks:
        verdict = "same" if math.isclose(real, teaching, rel_tol=1e-12) else "DIFFERENT"
        print(f"  {name:<36} real {real:10.4f}   teaching {teaching:10.4f}   {verdict}")
    print(f"  absolute_crossing(10, 1, 0, 40) gives {lab.absolute_crossing(10, 1, 0, 40)} (the curve tops out below 50 %)")
    short = lab.fit_hill([0.1, 1, 10, 100, 1000], [5, 14, 27, 35, 38])
    print(f"  fit_hill on the means 5, 14, 27, 35, 38 -> status {short['status']}")
    print(f"  direction: {short['direction']}")
    records, wells = lab.synthetic_data()
    print(f"  the practice plate holds {wells.size} well values (3 wells x {len(lab.DOSES_NM)} concentrations)")
    means = wells.mean(axis=1)
    fit = lab.fit_hill(lab.DOSES_NM, means)
    print(f"  fit_hill on the practice plate: status {fit['status']}, IC50 about {fit['absolute_ic50_nm']:.2f} nM, "
          f"pIC50 about {fit['pIC50']:.2f}, slope about {fit['hill_slope']:.2f}")
    print(f"  RMSE {fit['rmse_percentage_points']:.2f} percentage points, against {fit['rmse_constant_baseline']:.2f} for a flat baseline")
    interval = lab.bootstrap(lab.DOSES_NM, wells)
    low, high = interval["percentile_95_interval_nm"]
    print(f"  bootstrap: {interval['accepted']} of {interval['resamples']} refits accepted, middle 95 % from {low:.2f} to {high:.2f} nM")


def main():
    for example in (example_1_percent_inhibition, example_2_concentration, example_3_units, example_4_dilution,
                    example_5_controls, example_6_replicates, example_7_three_points, example_8_logarithm,
                    example_9_hill_formula, example_10_slope, example_11_relative_and_absolute,
                    example_12_potency_and_efficacy, example_13_cheng_prusoff, example_14_pic50,
                    example_15_practice_plate, example_16_error, example_17_search, example_18_residual_patterns,
                    example_19_bootstrap, example_20_bracketing, example_21_growth_rate, example_22_invented_rows,
                    example_23_bounds, example_24_assay_groups, example_25_exercises, example_26_real_code):
        example()
    print()
    print("Done. Change the numbers at the top of any example and run it again.")


if __name__ == "__main__":
    main()
