import os
import io
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from PIL import Image


def main():
    # Grid C configuration (match 00_generate_grid_c.py)
    num_bands = 8
    outer_radius = 1.0

    sector_parts = 1  # span two adjacent bands
    num_sectors = num_bands - sector_parts + 1  # no wrap-around => 7

    # Image parameters (match other generators)
    figsize = (5, 5)  # inches -> dpi=100 => 500x500 px
    dpi = 100
    output_folder = "stimuli/sectors_c"
    os.makedirs(output_folder, exist_ok=True)

    # Band boundaries in data coordinates (-outer_radius .. +outer_radius)
    y_boundaries = np.linspace(-outer_radius, outer_radius, num_bands + 1)

    sector_arrays = {}

    for step in range(num_sectors):
        y0 = y_boundaries[step]
        y1 = y_boundaries[step + sector_parts]
        height = y1 - y0
        if height <= 0:
            continue

        # Clip path circle (transparent)
        clip_circle = Circle((0, 0), outer_radius, fill=False, edgecolor="none")

        # Rectangle covering the sector's vertical span, spanning full x-range
        rect = Rectangle(
            (-outer_radius, y0),
            2 * outer_radius,
            height,
            facecolor="black",
            edgecolor="none",
        )

        # Create figure with transparent background
        fig = plt.figure(figsize=figsize, facecolor="none")
        ax = plt.gca()

        # Add clip path and apply it to the rectangle
        ax.add_patch(clip_circle)
        ax.add_patch(rect)
        rect.set_clip_path(clip_circle)

        # Match axis settings so it aligns with the other generators
        ax.set_aspect("equal")
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.axis("off")
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        filename = f"sector_c_{step:02d}.png"
        output_path = os.path.join(output_folder, filename)

        # Save to buffer first (then also extract alpha)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, pad_inches=0, transparent=True)
        plt.close(fig)

        # Write PNG file to disk
        with open(output_path, "wb") as f:
            f.write(buf.getvalue())

        # Extract alpha channel
        buf.seek(0)
        img = Image.open(buf).convert("RGBA")
        img_array = np.array(img)
        alpha_channel = img_array[:, :, 3] / 255.0  # normalize 0..1

        sector_arrays[f"sector_c_{step:02d}"] = alpha_channel
        print(f"Saved {filename}")

    # Save all sector alpha masks in one pickle
    combined_pickle_path = os.path.join(output_folder, "all_sectors_c.pkl")
    with open(combined_pickle_path, "wb") as f:
        pickle.dump(sector_arrays, f)

    print(f"\nAll {num_sectors} sector images saved to: {output_folder}")
    print(f"All sector arrays saved in: {combined_pickle_path}")
    print(f"Dictionary keys: {list(sector_arrays.keys())}")
    if sector_arrays:
        print(f"Array shape: {list(sector_arrays.values())[0].shape} (values 0-1)")


if __name__ == "__main__":
    main()