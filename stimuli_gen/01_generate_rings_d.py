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


def generate_annular_rings_d(num_rings=NUM_RINGS, outer_radius=OUTER_RADIUS, inner_radius=INNER_RADIUS, ring_parts=1):
    """
    Generate rings for Grid D where each ring is the union of `ring_parts`
    adjacent ring parts, represented as a single annulus between:
    inner_r = boundary before the first included ring part
    outer_r = outer boundary of the last included ring part
    """
    out_dir = os.path.join(OUTPUT_ROOT, OUTPUT_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    # Radii used by 00_generate_grid_d.py to draw ring outlines.
    # We'll use these as the "outer boundary" for ring parts:
    # ring-part p: inner=previous_r (0 then radii[p-1]) and outer=radii[p]
    num_ring_parts = num_rings
    ring_parts_group = int(ring_parts)
    if ring_parts_group < 1:
        raise ValueError(f"ring_parts must be >= 1, got {ring_parts}")
    if ring_parts_group > num_ring_parts:
        raise ValueError(
            f"ring_parts ({ring_parts_group}) cannot exceed number of ring parts ({num_ring_parts})"
        )
    num_annular_rings = num_ring_parts - ring_parts_group + 1  # no wrap-around

    radii = np.linspace(inner_radius, outer_radius, num_ring_parts)

    ring_alpha_dict = {}

    def save_ring_ring(inner_r, outer_r, idx):
        """Save one full 360-degree annulus between inner_r and outer_r."""
        width = outer_r - inner_r
        if width <= 0:
            return

        wedge = Wedge(
            (0, 0),
            outer_r,
            0.0,
            360.0,
            width=width,          # creates the annulus gap from inner_r to outer_r
            facecolor="black",
            edgecolor="none",
        )

        # Render to a transparent PNG and extract alpha
        fig = plt.figure(figsize=FIGSIZE, facecolor="none")
        ax = fig.add_subplot(111)  # avoid reliance on global "current axes"
        ax.add_patch(wedge)

        ax.set_aspect("equal")
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.axis("off")
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        buf = io.BytesIO()
        try:
            fig.canvas.draw()  # ensure rendering is complete before saving
            fig.savefig(buf, format="png", dpi=DPI, pad_inches=0, transparent=True)
        finally:
            plt.close(fig)

        filename = f"ring_d_{idx:02d}.png"
        out_path = os.path.join(out_dir, filename)

        # Write PNG to disk
        with open(out_path, "wb") as f:
            f.write(buf.getvalue())

        # Extract alpha channel for pickle
        buf.seek(0)
        im = Image.open(buf).convert("RGBA")
        arr = np.array(im)
        alpha = arr[:, :, 3] / 255.0  # normalize 0..1
        ring_alpha_dict[f"ring_d_{idx:02d}"] = alpha

        print(f"Saved {out_path}")

    # ring i spans ring parts [i, i+1, ..., i+ring_parts_group-1]
    # Ring part p boundaries:
    #   outer boundary = radii[p]
    #   inner boundary = 0.0 if p==0 else radii[p-1]
    #
    # Therefore ring i:
    #   inner_r = 0.0 if i==0 else radii[i-1]
    #   outer_r = radii[i+ring_parts_group-1]
    for i in range(num_annular_rings):
        inner_r = 0.0 if i == 0 else radii[i - 1]
        outer_r = radii[i + ring_parts_group - 1]
        save_ring_ring(inner_r, outer_r, i)

    # Save alpha masks dictionary
    pkl_path = os.path.join(out_dir, "all_rings_d.pkl")
    with open(pkl_path, "wb") as f:
        pickle.dump(ring_alpha_dict, f)

    print(f"\nAll {num_annular_rings} annular rings saved to: {out_dir}")
    print(f"Alpha masks saved in: {pkl_path}")
    print(f"Dictionary keys: {list(ring_alpha_dict.keys())}")

    return ring_alpha_dict


if __name__ == "__main__":
    generate_annular_rings_d()