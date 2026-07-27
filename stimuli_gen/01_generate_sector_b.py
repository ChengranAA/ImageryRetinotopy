import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import os
import numpy as np
import pickle
import io
from PIL import Image

if __name__ == "__main__":
    # Parameters matching grid_b exactly
    num_grid_parts = 8
    sector_parts = 2  # each sector spans two adjacent grid parts
    outer_radius = 1.0

    # Number of sliding sectors across the 8 vertical parts:
    # [0,1], [1,2], ..., [6,7]
    num_sectors = num_grid_parts - sector_parts + 1

    # Image parameters matching grid exactly
    figsize = (5, 5)  # 5x5 inches
    dpi = 100         # 100 DPI = 500x500 pixels
    output_folder = 'stimuli/sectors_b'

    # Dictionary to store all sector arrays
    sector_arrays = {}

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Vertical grid boundaries matching 00_generate_grid_b.py
    x_boundaries = np.linspace(-outer_radius, outer_radius, num_grid_parts + 1)

    def generate_sector_and_save(step):
        # Sector spans two adjacent vertical grid parts
        x0 = x_boundaries[step]
        x1 = x_boundaries[step + sector_parts]
        sector_width = x1 - x0

        # Rectangle covering two adjacent bars, clipped to the circle
        rect = Rectangle(
            (x0, -outer_radius),
            sector_width,
            2 * outer_radius,
            facecolor='black',
            edgecolor='none'
        )

        # Circle clip path
        clip_circle = Circle((0, 0), outer_radius, fill=False, edgecolor='none')

        # Create figure with transparent background
        plt.figure(figsize=figsize, facecolor='none')
        ax = plt.gca()

        # Add clip circle and rectangle
        ax.add_patch(clip_circle)
        ax.add_patch(rect)
        rect.set_clip_path(clip_circle)

        # Set aspect ratio and limits exactly like grid
        ax.set_aspect('equal')
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.axis('off')

        # Set fixed boundaries to ensure exact 500x500 pixels
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Save PNG image
        filename = f'sector_b_{step:02d}.png'
        output_path = os.path.join(output_folder, filename)

        # Save to buffer first to get numpy array
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=dpi, pad_inches=0, transparent=True)

        # Save PNG file
        with open(output_path, 'wb') as f:
            f.write(buf.getvalue())

        # Convert buffer to numpy array
        buf.seek(0)
        img = Image.open(buf)
        img_array = np.array(img)

        # Extract alpha channel (black sector = 1, transparent = 0)
        if img_array.shape[2] == 4:  # RGBA
            alpha_channel = img_array[:, :, 3] / 255.0
        else:
            alpha_channel = np.mean(img_array[:, :, :3], axis=2) / 255.0

        # Store in dictionary
        sector_arrays[f'sector_b_{step:02d}'] = alpha_channel

        plt.close()

        print(f'Saved {filename}')

    # Generate all sliding two-part vertical sectors
    for step in range(num_sectors):
        generate_sector_and_save(step)

    # Save all sector arrays in one pickle file as dictionary
    combined_pickle_path = os.path.join(output_folder, 'all_sectors_b.pkl')
    with open(combined_pickle_path, 'wb') as f:
        pickle.dump(sector_arrays, f)

    print(f'\nAll {num_sectors} sector images saved to: {output_folder}')
    print(f'Image size: {figsize[0]*dpi} x {figsize[1]*dpi} pixels ({figsize[0]}x{figsize[1]} inches at {dpi} DPI)')
    print(f'All sector arrays saved in: {combined_pickle_path}')
    print(f'Dictionary keys: {list(sector_arrays.keys())}')
    print(f'Array shape: {list(sector_arrays.values())[0].shape} (values 0-1)')