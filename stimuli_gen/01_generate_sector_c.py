"""Generate alpha masks for sliding horizontal bands in Grid C."""

import os
import io
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from PIL import Image


def main():
    # Grid C configuration (match 00_generate_grid_c.py)
    number_of_grid_bands = 8
    outer_radius = 1.0

    bands_per_mask = 2
    number_of_masks = number_of_grid_bands - bands_per_mask + 1

    # Image parameters (match other generators)
    figure_size_inches = (5, 5)
    image_dpi = 100
    output_directory = "stimuli/sectors_c"
    os.makedirs(output_directory, exist_ok=True)

    # Band boundaries in data coordinates (-outer_radius .. +outer_radius)
    horizontal_boundaries = np.linspace(-outer_radius, outer_radius, number_of_grid_bands + 1)

    sector_masks = {}

    for mask_index in range(number_of_masks):
        lower_boundary = horizontal_boundaries[mask_index]
        upper_boundary = horizontal_boundaries[mask_index + bands_per_mask]
        band_height = upper_boundary - lower_boundary
        if band_height <= 0:
            continue

        # Clip path circle (transparent)
        circular_clip_path = Circle((0, 0), outer_radius, fill=False, edgecolor="none")

        # Rectangle covering the mask's vertical span, spanning the full x-range.
        band_patch = Rectangle(
            (-outer_radius, lower_boundary),
            2 * outer_radius,
            band_height,
            facecolor="black",
            edgecolor="none",
        )

        # Create figure with transparent background
        figure, axes = plt.subplots(figsize=figure_size_inches, facecolor="none")

        # Add clip path and apply it to the rectangle
        axes.add_patch(circular_clip_path)
        axes.add_patch(band_patch)
        band_patch.set_clip_path(circular_clip_path)

        # Match axis settings so it aligns with the other generators
        axes.set_aspect("equal")
        axes.set_xlim(-1.1, 1.1)
        axes.set_ylim(-1.1, 1.1)
        axes.axis("off")
        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        filename = f"sector_c_{mask_index:02d}.png"
        output_path = os.path.join(output_directory, filename)

        # Save to a buffer first, then extract its alpha channel.
        png_buffer = io.BytesIO()
        figure.savefig(png_buffer, format="png", dpi=image_dpi, pad_inches=0, transparent=True)
        plt.close(figure)

        # Write PNG file to disk
        with open(output_path, "wb") as output_file:
            output_file.write(png_buffer.getvalue())

        # Extract alpha channel
        png_buffer.seek(0)
        rgba_image = Image.open(png_buffer).convert("RGBA")
        alpha_mask = np.asarray(rgba_image)[:, :, 3] / 255.0

        sector_masks[f"sector_c_{mask_index:02d}"] = alpha_mask
        print(f"Saved {filename}")

    # Save all sector alpha masks in one pickle archive.
    mask_archive_path = os.path.join(output_directory, "all_sectors_c.pkl")
    with open(mask_archive_path, "wb") as output_file:
        pickle.dump(sector_masks, output_file)

    print(f"\nAll {number_of_masks} sector images saved to: {output_directory}")
    print(f"All sector masks saved in: {mask_archive_path}")
    print(f"Dictionary keys: {list(sector_masks.keys())}")
    if sector_masks:
        print(f"Mask shape: {next(iter(sector_masks.values())).shape} (values 0-1)")


if __name__ == "__main__":
    main()
