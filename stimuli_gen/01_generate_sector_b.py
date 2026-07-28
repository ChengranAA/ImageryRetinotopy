"""Generate alpha masks for sliding vertical bands in Grid B."""

import io
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from PIL import Image


NUMBER_OF_GRID_BANDS = 8
BANDS_PER_MASK = 2
OUTER_RADIUS = 1.0
FIGURE_SIZE_INCHES = (5, 5)
IMAGE_DPI = 100
OUTPUT_DIRECTORY = "stimuli/sectors_b"


def render_vertical_band_mask(left_boundary, right_boundary):
    """Render a circle-clipped vertical band and return PNG bytes and alpha mask."""
    band_width = right_boundary - left_boundary
    circular_clip_path = Circle((0, 0), OUTER_RADIUS, fill=False, edgecolor="none")
    band_patch = Rectangle((left_boundary, -OUTER_RADIUS), band_width, 2 * OUTER_RADIUS,
                           facecolor="black", edgecolor="none")
    figure, axes = plt.subplots(figsize=FIGURE_SIZE_INCHES, facecolor="none")
    axes.add_patch(circular_clip_path)
    axes.add_patch(band_patch)
    band_patch.set_clip_path(circular_clip_path)
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
    png_bytes = png_buffer.getvalue()
    png_buffer.seek(0)
    alpha_mask = np.asarray(Image.open(png_buffer).convert("RGBA"))[:, :, 3] / 255.0
    return png_bytes, alpha_mask


def main():
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    vertical_boundaries = np.linspace(-OUTER_RADIUS, OUTER_RADIUS, NUMBER_OF_GRID_BANDS + 1)
    number_of_masks = NUMBER_OF_GRID_BANDS - BANDS_PER_MASK + 1
    sector_masks = {}
    for mask_index in range(number_of_masks):
        left_boundary = vertical_boundaries[mask_index]
        right_boundary = vertical_boundaries[mask_index + BANDS_PER_MASK]
        filename = f"sector_b_{mask_index:02d}.png"
        png_bytes, alpha_mask = render_vertical_band_mask(left_boundary, right_boundary)
        with open(os.path.join(OUTPUT_DIRECTORY, filename), "wb") as output_file:
            output_file.write(png_bytes)
        sector_masks[f"sector_b_{mask_index:02d}"] = alpha_mask
        print(f"Saved {filename}")
    mask_archive_path = os.path.join(OUTPUT_DIRECTORY, "all_sectors_b.pkl")
    with open(mask_archive_path, "wb") as output_file:
        pickle.dump(sector_masks, output_file)


if __name__ == "__main__":
    main()
