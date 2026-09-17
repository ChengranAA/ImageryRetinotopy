#!/usr/bin/env python3
"""
00_generate_ring_grid.py

Generate a circular grid consisting of 6 concentric rings and save as a 500x500 PNG
with a transparent background. All rings except the outermost one are drawn with
a dashed line style; the outermost ring is drawn solid (slightly thicker).

Output file: stimuli/ring_grid.png

Usage:
    python stimuli_gen/00_generate_ring_grid.py
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def main():
    # Parameters
    num_rings = 6
    outer_radius = 1.0
    # Choose an inner radius > 0 to avoid drawing a degenerate center point
    inner_radius = outer_radius / (num_rings * 2.0)

    # Image parameters (results in 500x500 px)
    figsize = (5, 5)  # inches
    dpi = 100
    output_folder = "stimuli"
    output_filename = "ring_grid.png"
    output_path = os.path.join(output_folder, output_filename)

    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Create figure with transparent background
    plt.figure(figsize=figsize, facecolor="none")
    ax = plt.gca()

    # Compute radii evenly spaced between inner_radius and outer_radius
    radii = np.linspace(inner_radius, outer_radius, num_rings)

    # Draw concentric rings:
    # - All rings except the outermost use a dashed linestyle ("--")
    # - The outermost ring is solid and slightly thicker to emphasize the boundary
    for i, r in enumerate(radii):
        is_outermost = (i == len(radii) - 1)
        linestyle = "-" if is_outermost else "--"
        linewidth = 1.6 if is_outermost else 1.0

        ring = Circle(
            (0, 0),
            r,
            fill=False,
            linestyle=linestyle,
            color="black",
            linewidth=linewidth,
        )
        ax.add_patch(ring)

    # Set aspect ratio and limits so the circle is centered and occupies the canvas
    ax.set_aspect("equal")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis("off")

    # Ensure edges occupy full canvas so PNG is exactly 500x500
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save PNG with transparent background
    plt.savefig(output_path, dpi=dpi, pad_inches=0, transparent=True)
    plt.close()

    print(f"Saved {output_filename} to {output_folder}")
    print(f"Image size: {figsize[0]*dpi:.0f} x {figsize[1]*dpi:.0f} pixels")


if __name__ == "__main__":
    main()
