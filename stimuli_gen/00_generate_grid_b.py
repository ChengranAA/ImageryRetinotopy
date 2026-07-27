#!/usr/bin/env python3
"""
Generate a circular grid divided vertically into 8 equal-width portions.

This script creates a 500x500 PNG with a transparent background. The circle
is drawn with an outer radius of 1.0 in normalized figure coordinates and
vertical dividing lines are drawn only across the circle (i.e., clipped
to the circle's extent by computing y-limits for each vertical line).

Output file: stimuli/sector_grid_b.png
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

def main():
    # Parameters
    num_vertical_parts = 8
    outer_radius = 1.0

    # Image parameters
    figsize = (5, 5)  # inches -> with dpi=100 this gives 500x500 px
    dpi = 100
    output_folder = "stimuli"
    output_filename = "sector_grid_b.png"
    output_path = os.path.join(output_folder, output_filename)

    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Create figure with transparent background
    plt.figure(figsize=figsize, facecolor="none")
    ax = plt.gca()

    # Compute vertical boundary x positions
    x_boundaries = np.linspace(-outer_radius, outer_radius, num_vertical_parts + 1)

    # Draw vertical lines clipped to the circle by computing y-limits
    for x in x_boundaries:
        # For |x| > outer_radius numerical rounding can cause negative inside sqrt; guard it
        inside = max(0.0, outer_radius**2 - x**2)
        y_limit = np.sqrt(inside)
        ax.plot([x, x], [-y_limit, y_limit], linestyle="--", color="black", linewidth=1.0)

    # Draw outer circle
    circle = Circle((0, 0),
                    outer_radius,
                    fill=False,
                    linestyle="-",
                    color="black",
                    linewidth=1.0)
    ax.add_patch(circle)

    # Set aspect ratio and limits
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