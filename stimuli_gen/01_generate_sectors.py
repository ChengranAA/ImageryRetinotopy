"""Generate alpha masks for the pilot radial-sector stimulus grid."""

import io
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge
from PIL import Image


NUMBER_OF_SECTORS = 12
INNER_RADIUS = 0.0
OUTER_RADIUS = 1.0
SECTOR_STEP_DEGREES = 360.0 / NUMBER_OF_SECTORS
SECTOR_WIDTH_DEGREES = 360.0 / 6
FIGURE_SIZE_INCHES = (5, 5)
IMAGE_DPI = 100
OUTPUT_DIRECTORY = "stimuli/sectors_pilot"


def alpha_mask_from_png(png_buffer):
    """Return the normalized alpha channel from a rendered PNG buffer."""
    png_buffer.seek(0)
    rgba_image = Image.open(png_buffer).convert("RGBA")
    return np.asarray(rgba_image)[:, :, 3] / 255.0


def render_sector_mask(sector_index):
    """Render one radial sector and return its PNG bytes and alpha mask."""
    start_angle_degrees = sector_index * SECTOR_STEP_DEGREES
    end_angle_degrees = start_angle_degrees + SECTOR_WIDTH_DEGREES
    sector_patch = Wedge(
        (0, 0), OUTER_RADIUS, start_angle_degrees, end_angle_degrees,
        width=OUTER_RADIUS - INNER_RADIUS, facecolor="black", edgecolor="none",
    )
    figure, axes = plt.subplots(figsize=FIGURE_SIZE_INCHES, facecolor="none")
    axes.add_patch(sector_patch)
    axes.set_aspect("equal")
    axes.set_xlim(-1.1, 1.1)
    axes.set_ylim(-1.1, 1.1)
    axes.axis("off")
    figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

    png_buffer = io.BytesIO()
    try:
        figure.savefig(png_buffer, format="png", dpi=IMAGE_DPI, pad_inches=0, transparent=True)
    finally:
        plt.close(figure)
    return png_buffer.getvalue(), alpha_mask_from_png(png_buffer)


def main():
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    sector_masks = {}
    for sector_index in range(NUMBER_OF_SECTORS):
        filename = f"sector_{sector_index:02d}.png"
        png_bytes, alpha_mask = render_sector_mask(sector_index)
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "wb") as output_file:
            output_file.write(png_bytes)
        sector_masks[f"sector_{sector_index:02d}"] = alpha_mask
        print(f"Saved {filename}")

    mask_archive_path = os.path.join(OUTPUT_DIRECTORY, "all_sectors.pkl")
    with open(mask_archive_path, "wb") as output_file:
        pickle.dump(sector_masks, output_file)
    print(f"\nAll {NUMBER_OF_SECTORS} sector images saved to: {OUTPUT_DIRECTORY}")
    print(f"All sector masks saved in: {mask_archive_path}")


if __name__ == "__main__":
    main()
