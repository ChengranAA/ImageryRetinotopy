import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
import os
import numpy as np
import pickle
import io
from PIL import Image

if __name__ == "__main__":
    # Parameters matching grid exactly
    num_sectors = 12
    inner_radius = 0.0  # Same as grid
    outer_radius = 1.0   # Same as grid
    step_angle = 360.0 / 12
    sector_angle = 360.0 / 6  # 22.5 degrees

    # Image parameters matching grid exactly
    figsize = (5, 5)  # 5x5 inches
    dpi = 100         # 100 DPI = 500x500 pixels
    output_folder = 'stimuli/sectors_a_pilot'

    # Dictionary to store all sector arrays
    sector_arrays = {}

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    def generate_sector_and_save(step):
        # Create wedge with same parameters as grid
        # Wedge goes from inner_radius to outer_radius (not center to outer_radius)
        start_angle = step * step_angle
        end_angle = start_angle + sector_angle

        wedge = Wedge((0, 0), outer_radius,
                     start_angle, end_angle,
                     width=outer_radius - inner_radius,  # Creates gap in center
                     facecolor='black',
                     edgecolor='none')

        # Create figure with transparent background
        plt.figure(figsize=figsize, facecolor='none')
        ax = plt.gca()
        ax.add_patch(wedge)

        # Set aspect ratio and limits exactly like grid
        ax.set_aspect('equal')
        # Use same limits as grid file
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.axis('off')

        # Set fixed boundaries to ensure exact 500x500 pixels
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Save PNG image
        filename = f'sector_a_{step:02d}.png'
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

        # Extract alpha channel (black wedge = 1, transparent = 0)
        # For transparent PNG: black wedge has alpha=255, transparent areas have alpha=0
        if img_array.shape[2] == 4:  # RGBA
            alpha_channel = img_array[:, :, 3] / 255.0  # Normalize to 0-1
        else:
            # Convert RGB to grayscale if no alpha channel
            alpha_channel = np.mean(img_array[:, :, :3], axis=2) / 255.0

        # Store in dictionary
        sector_arrays[f'sector_a_{step:02d}'] = alpha_channel

        plt.close()

        print(f'Saved {filename}')

    # Generate all 16 sectors
    for step in range(num_sectors):
        generate_sector_and_save(step)

    # Save all sector arrays in one pickle file as dictionary
    combined_pickle_path = os.path.join(output_folder, 'all_sectors_a.pkl')
    with open(combined_pickle_path, 'wb') as f:
        pickle.dump(sector_arrays, f)

    print(f'\nAll {num_sectors} sector images saved to: {output_folder}')
    print(f'Image size: {figsize[0]*dpi} x {figsize[1]*dpi} pixels ({figsize[0]}x{figsize[1]} inches at {dpi} DPI)')
    print(f'All sector arrays saved in: {combined_pickle_path}')
    print(f'Dictionary keys: {list(sector_arrays.keys())}')
    print(f'Array shape: {list(sector_arrays.values())[0].shape} (values 0-1)')