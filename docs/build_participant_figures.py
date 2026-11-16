"""Build participant teaching figures from the experiment's actual PNG assets.

Run from any directory with the project's Python environment. Teaching diagrams
use a simplified background; their printed size is not a visual-angle calibration.
"""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "participant_figures"
OUT.mkdir(exist_ok=True)
INK = "#21313f"
BLUE = "#246b9e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "text.color": INK, "axes.titlecolor": INK,
                     "savefig.facecolor": "white"})
GRIDS = {"sector": "sector_grid_pilot.png", "vertical": "vertical_bar_grid.png",
         "horizontal": "horizontal_bar_grid.png"}


def target(ax, radius=0.018):
    ax.add_patch(Circle((0, 0), radius, color="white", zorder=6))
    ax.add_patch(Circle((0, 0), radius * 5 / 8, color="green", zorder=7))


def screen(ax, kind="sector", position=None, opacity=1):
    ax.set_aspect("equal")
    ax.set_xlim(-1.31, 1.31)
    ax.set_ylim(-1.31, 1.31)
    ax.axis("off")
    ax.add_patch(Circle((0, 0), 1.10, color="#d8d8d8", zorder=0))
    grid = Image.open(ROOT / "stimuli" / GRIDS[kind])
    ax.imshow(grid, extent=(-1.1, 1.1, -1.1, 1.1), zorder=1)
    if position is not None:
        directory = "sectors_pilot" if kind == "sector" else f"{kind}_bars"
        prefix = "sector" if kind == "sector" else f"{kind}_bar"
        mask = Image.open(ROOT / "stimuli" / directory / f"{prefix}_{position:02d}.png")
        ax.imshow(mask, extent=(-1.1, 1.1, -1.1, 1.1), alpha=opacity, zorder=2)
    target(ax)


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def curved_direction(ax, clockwise):
    theta1, theta2 = (15, 75) if clockwise else (105, 165)
    ax.add_patch(Arc((0, 0), 2.35, 2.35, theta1=theta1, theta2=theta2,
                     color=BLUE, lw=2.2))
    end_angle = theta1 if clockwise else theta2
    before = end_angle + 9 if clockwise else end_angle - 9
    def point(deg):
        rad = math.radians(deg)
        return 1.175 * math.cos(rad), 1.175 * math.sin(rad)
    ax.annotate("", xy=point(end_angle), xytext=point(before),
                arrowprops={"arrowstyle": "-|>", "color": BLUE, "lw": 2.2})


# 1. A fixation target in context, and a clearly marked enlarged view.
fig, axes = plt.subplots(1, 2, figsize=(9, 2.3))
for ax in axes:
    ax.set_aspect("equal")
    ax.axis("off")
axes[0].set_xlim(-2.3, 2.3)
axes[0].set_ylim(-1.2, 1.2)
axes[0].add_patch(plt.Rectangle((-2.2, -1.05), 4.4, 2.1, color="#a0a0a0"))
target(axes[0], radius=0.065)
axes[0].set_title("Keep your gaze at the centre", fontsize=12)
axes[1].set_xlim(-1.9, 1.9)
axes[1].set_ylim(-1.2, 1.2)
axes[1].add_patch(plt.Rectangle((-1.8, -1.05), 3.6, 2.1, color="#a0a0a0"))
target(axes[1], radius=0.60)
axes[1].annotate("White outer ring", xy=(0.47, 0.30), xytext=(0.85, 0.75),
                 fontsize=10, ha="center", arrowprops={"arrowstyle": "-", "color": INK})
axes[1].annotate("Green centre", xy=(0.05, -0.1), xytext=(1.0, -0.75),
                 fontsize=10, ha="center", arrowprops={"arrowstyle": "-", "color": INK})
axes[1].set_title("Enlarged fixation target", fontsize=12)
fig.subplots_adjust(wspace=0.08)
save(fig, "01_fixation.png")

# 2. Fixed trial order, with actual starting masks and movement directions.
fig, axes = plt.subplots(1, 4, figsize=(11, 3.3))
items = [("sector", 2, "1. Clockwise sector", "Start at top"),
         ("vertical", 0, "2. Vertical bar", "Left to right, then back"),
         ("horizontal", 0, "3. Horizontal bar", "Bottom to top, then back"),
         ("sector", 2, "4. Counterclockwise sector", "Start at top")]
for i, (ax, (kind, position, title, subtitle)) in enumerate(zip(axes, items)):
    screen(ax, kind, position)
    ax.set_title(title, fontsize=10.5, fontweight="bold", pad=10)
    ax.text(0, -1.42, subtitle, ha="center", fontsize=9)
    if kind == "sector":
        curved_direction(ax, clockwise=i == 0)
    elif kind == "vertical":
        ax.annotate("", xy=(0.65, -1.17), xytext=(-0.65, -1.17),
                    arrowprops={"arrowstyle": "<->", "color": BLUE, "lw": 2})
    else:
        ax.annotate("", xy=(1.16, 0.65), xytext=(1.16, -0.65),
                    arrowprops={"arrowstyle": "<->", "color": BLUE, "lw": 2})
fig.subplots_adjust(wspace=0.15)
save(fig, "02_trial_order.png")

# 3. Every cued sector position, beginning at the top in either direction.
fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
for ax, clockwise in zip(axes, (True, False)):
    screen(ax, "sector", 2)
    for i in range(12):
        angle = math.radians(90 + (-30 if clockwise else 30) * i)
        ax.text(1.19 * math.cos(angle), 1.19 * math.sin(angle), str(i + 1),
                ha="center", va="center", fontsize=11, fontweight="bold", color=BLUE)
    ax.set_title("Clockwise: first trial" if clockwise else "Counterclockwise: last trial",
                 fontsize=13, pad=18)
fig.subplots_adjust(wspace=0.2)
save(fig, "03_sector_directions.png")

# 4. Complete bar cycles: seven positions, one outside step, return, outside.
sequence = [*range(7), None, *range(6, -1, -1), None]
fig, axes = plt.subplots(4, 8, figsize=(13, 7.1))
for kind_index, kind in enumerate(("vertical", "horizontal")):
    for i, position in enumerate(sequence):
        ax = axes[kind_index * 2 + i // 8, i % 8]
        screen(ax, kind, position)
        ax.set_title(f"Step {i + 1}", fontsize=9, pad=1)
        if position is None:
            ax.text(0, -1.30, "OUTSIDE", color=BLUE, fontsize=9,
                    fontweight="bold", ha="center", va="top")
    fig.text(0.5, 0.99 if kind_index == 0 else 0.495,
             "VERTICAL BAR: left to right, outside, then back" if kind == "vertical"
             else "HORIZONTAL BAR: bottom to top, outside, then back",
             ha="center", va="top", fontsize=12, fontweight="bold")
fig.subplots_adjust(left=0.015, right=0.985, top=0.925, bottom=0.025, hspace=0.66, wspace=0.12)
save(fig, "04_bar_cycles.png")

# 5. These panels represent the actual visible content in each run mode.
fig, axes = plt.subplots(3, 3, figsize=(9, 6.5))
rows = [("Visual guide\n+ imagery", [True, False, False]),
        ("Pure imagery", [False, False, False]),
        ("Visual\nperception", [True, True, True])]
for row, (label, visible) in enumerate(rows):
    for col, watch in enumerate(visible):
        ax = axes[row, col]
        screen(ax, "sector", 2 if watch else None)
        action = "WATCH" if watch else "IMAGINE"
        if row == 0 and col == 0:
            action += " (fading guide)"
        ax.set_title(f"Cycle {col + 1}: {action}", fontsize=10.5, pad=1,
                     color=INK if watch else BLUE)
        if col == 0:
            ax.text(-1.65, 0, label, ha="right", va="center", fontsize=11,
                    fontweight="bold", transform=ax.transData)
        if col < 2:
            ax.annotate("", xy=(1.66, 0), xytext=(1.35, 0), annotation_clip=False,
                        arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.5})
fig.subplots_adjust(left=0.20, right=0.97, top=0.96, bottom=0.02, hspace=0.35, wspace=0.35)
save(fig, "05_run_types.png")
print(f"Wrote five participant figures to {OUT}")
