#!/usr/bin/env python3
"""worked_examples.py - the small calculations from Part 1 of the video, reproduced step by step.

What it does
    The video explains training and attention with tiny examples you can follow with a calculator.
    This script runs the same examples, so you can check every number and then change the inputs to see what happens:

      1. Loss as a penalty:        loss = -ln(probability given to the correct answer)
      2. Gradient descent:         one knob, loss = (knob - 3)^2, learning rate 0.1
      3. Attention with 3 positions: query, keys, scores, softmax weights, blended values
      4. Reading the saved attention weights of the EGFR run (optional, needs the file data/esm2/egfr/attention.npy)

What it needs
    Python 3.9 or newer and numpy. Nothing is downloaded and no model is run.

What to expect
    The numbers printed below match the video (rounded):
      loss for probability 0.2 -> 1.61 and for 0.8 -> 0.22
      knob 0 -> 0.6 -> 1.08 -> 1.46 with losses 9.00, 5.76, 3.69, 2.36
      attention weights about 41%, 20%, 38% and a blended list of about [1.21, 0.79]

Run it from the folder that holds `code/` and `data/`:
    python code/worked_examples.py
"""
import os
import numpy as np


def show_loss_examples():
    """Part 1 of the video: the loss is -ln(p), where p is the probability the model gives to the correct answer."""
    print("1. Loss = -ln(probability of the correct answer)")
    for p in (0.2, 0.8):
        # np.log is the natural logarithm (base e); the minus sign turns a negative number into a positive penalty
        print(f"   p = {p:.1f}  ->  loss = {-np.log(p):.2f}")
    print("   A confident correct answer (p near 1) gives a loss near 0; a very small p gives a large loss.\n")


def gradient_descent_one_knob(start=0.0, best=3.0, learning_rate=0.1, steps=3):
    """Part 3 of the video: walk downhill on loss = (knob - best)^2, one knob only."""
    print(f"2. Gradient descent on one knob, loss = (knob - {best:g})^2, learning rate {learning_rate:g}")
    knob = start
    for step in range(steps + 1):
        loss = (knob - best) ** 2
        slope = 2 * (knob - best)  # the derivative of the loss with respect to the knob
        print(f"   step {step}: knob = {knob:.2f}  loss = {loss:.2f}  slope = {slope:+.2f}")
        knob = knob - learning_rate * slope  # move a little in the direction that lowers the loss
    print("   Each step is smaller than the one before, because the slope flattens near the best value.")
    print("   Try learning_rate=1.1 to see the knob overshoot the valley, or 0.01 to see a very slow walk.\n")


def softmax(scores):
    """Turn scores into positive weights that add up to 1 (100 percent)."""
    e = np.exp(scores - np.max(scores))  # subtracting the maximum keeps the numbers safe and does not change the result
    return e / e.sum()


def attention_three_positions():
    """Part 3 of the video: one position decides how much to listen to three positions (all numbers are made up)."""
    print("3. Attention with three positions (lists of two numbers)")
    query = np.array([1.0, 0.0])                                    # what this position is looking for
    keys = np.array([[1.0, 0.2], [0.0, 1.0], [0.9, -0.1]])          # what each position offers
    values = np.array([[2.0, 0.0], [0.0, 2.0], [1.0, 1.0]])         # the information each position shares
    scores = keys @ query                                           # dot product of the query with every key
    scaled = scores / np.sqrt(len(query))                           # divide by the square root of the list length (about 1.41)
    weights = softmax(scaled)                                       # weights that add up to 100 percent
    blended = weights @ values                                      # blend the values in proportion to the weights
    print(f"   scores            = {np.round(scores, 2)}")
    print(f"   scaled scores     = {np.round(scaled, 2)}")
    print(f"   attention weights = {np.round(weights * 100, 0)} percent (sum = {weights.sum() * 100:.0f})")
    print(f"   blended list      = {np.round(blended, 2)}")
    print("   The first and third positions have keys that match the query, so they receive the most attention.\n")


def read_saved_attention(path="data/esm2/egfr/attention.npy"):
    """Part 4 of the video: the saved attention weights of ESM-2 (6 blocks x 20 heads x 63 x 63) for the EGFR window."""
    print("4. Reading the saved attention weights of the EGFR run")
    if not os.path.exists(path):
        print(f"   (skipped: {path} was not found; run this script from the folder that holds data/)\n")
        return
    attention = np.load(path)                                       # shape: block, head, row position, column position
    blocks, heads, rows, cols = attention.shape
    print(f"   shape = {attention.shape}: {blocks} blocks x {heads} heads, each a {rows} x {cols} table of weights")
    # Every row is one position dividing 100 percent of its attention among all positions, so each row adds up to 1.
    print(f"   every row adds up to 1: min {attention.sum(-1).min():.4f}, max {attention.sum(-1).max():.4f}")
    block, head = blocks - 1, 0                                      # the first head of the last block, as an example
    table = attention[block, head]
    row = 30                                                         # position 30 of the 63 tokens (token 0 is the start token)
    top = np.argsort(table[row])[::-1][:3]
    print(f"   block {block + 1}, head {head + 1}, row {row}: the strongest columns are {top.tolist()} "
          f"with weights {[round(float(v), 3) for v in table[row][top]]}")
    diagonal = np.mean(np.diag(table))                               # how much the average position listens to itself
    print(f"   average weight on the diagonal (positions listening to themselves): {diagonal:.3f}")
    print("   To draw the map: matplotlib.pyplot.imshow(table), then add colorbar() and axis labels.\n")


if __name__ == "__main__":
    show_loss_examples()
    gradient_descent_one_knob()
    attention_three_positions()
    read_saved_attention()
