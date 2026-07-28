import os
import io
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from PIL import Image


# Image/generation parameters (keep consistent with other scripts)
FIGSIZE = (5, 5)   # inches -> with DPI=100 => 500x500 px
DPI = 100
OUTPUT_ROOT = "stimuli"
OUTPUT_SUBDIR = "rings_d"

# Grid D parameters (as used in 00_generate_grid_d.py)
NUM_RINGS = 6
OUTER_RADIUS = 1.0
INNER_RADIUS = OUTER_RADIUS / (NUM_RINGS * 2.0)


def generate_annular_rings_d(
    number_of_rings=NUM_RINGS,
    outer_radius=OUTER_RADIUS,
    inner_radius=INNER_RADIUS,
    segments_per_mask=1,
):
    """
    Generate Grid D masks as annuli spanning adjacent radial segments.
    """
    out_dir = os.path.join(OUTPUT_ROOT, OUTPUT_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    # Radii used by 00_generate_grid_d.py to draw ring outlines.
    # We'll use these as the "outer boundary" for ring parts:
    # Segment p has the radial range 0/radii[p - 1] through radii[p].
    number_of_segments = number_of_rings
    mask_segment_count = int(segments_per_mask)
    if mask_segment_count < 1:
        raise ValueError(f"segments_per_mask must be >= 1, got {segments_per_mask}")
    if mask_segment_count > number_of_segments:
        raise ValueError(
            "segments_per_mask "
            f"({mask_segment_count}) cannot exceed number of segments ({number_of_segments})"
        )
    number_of_masks = number_of_segments - mask_segment_count + 1

    segment_outer_radii = np.linspace(inner_radius, outer_radius, number_of_segments)

    ring_masks = {}

    def save_annular_mask(inner_radius, outer_radius, mask_index):
        """Save one full annular mask between the specified radial boundaries."""
        annulus_width = outer_radius - inner_radius
        if annulus_width <= 0:
            return

        annulus_patch = Wedge(
            (0, 0),
            outer_radius,
            0.0,
            360.0,
            width=annulus_width,
            facecolor="black",
            edgecolor="none",
        )

        # Render to a transparent PNG and extract alpha
        figure = plt.figure(figsize=FIGSIZE, facecolor="none")
        axes = figure.add_subplot(111)
        axes.add_patch(annulus_patch)

        axes.set_aspect("equal")
        axes.set_xlim(-1.1, 1.1)
        axes.set_ylim(-1.1, 1.1)
        axes.axis("off")
        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        png_buffer = io.BytesIO()
        try:
            figure.canvas.draw()
            figure.savefig(png_buffer, format="png", dpi=DPI, pad_inches=0, transparent=True)
        finally:
            plt.close(figure)

        filename = f"ring_d_{mask_index:02d}.png"
        output_path = os.path.join(out_dir, filename)

        # Write PNG to disk
        with open(output_path, "wb") as output_file:
            output_file.write(png_buffer.getvalue())

        # Extract alpha channel for pickle
        png_buffer.seek(0)
        rgba_image = Image.open(png_buffer).convert("RGBA")
        alpha_mask = np.asarray(rgba_image)[:, :, 3] / 255.0
        ring_masks[f"ring_d_{mask_index:02d}"] = alpha_mask

        print(f"Saved {output_path}")

    for mask_index in range(number_of_masks):
        mask_inner_radius = 0.0 if mask_index == 0 else segment_outer_radii[mask_index - 1]
        mask_outer_radius = segment_outer_radii[mask_index + mask_segment_count - 1]
        save_annular_mask(mask_inner_radius, mask_outer_radius, mask_index)

    # Save alpha masks dictionary
    pkl_path = os.path.join(out_dir, "all_rings_d.pkl")
    with open(pkl_path, "wb") as output_file:
        pickle.dump(ring_masks, output_file)

    print(f"\nAll {number_of_masks} annular rings saved to: {out_dir}")
    print(f"Alpha masks saved in: {pkl_path}")
    print(f"Dictionary keys: {list(ring_masks.keys())}")

    return ring_masks


if __name__ == "__main__":
    generate_annular_rings_d()
