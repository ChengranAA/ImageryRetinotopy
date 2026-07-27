import matplotlib.pyplot as plt
import numpy as np
import os

if __name__ == "__main__":
    # Parameters
    num_sectors = 12
    inner_radius = 0.05
    outer_radius = 1.0

    # Image parameters
    figsize = (5, 5)  # 5x5 inches
    dpi = 100         # 100 DPI = 500x500 pixels
    output_folder = 'stimuli'

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Create figure with transparent background
    plt.figure(figsize=figsize, facecolor='none')
    ax = plt.gca()

    # Generate radial sector lines
    angles = np.linspace(0, 2 * np.pi, num_sectors + 1)[:-1]

    for angle in angles:
        x_start, y_start = inner_radius * np.cos(angle), inner_radius * np.sin(angle)
        x_end, y_end = outer_radius * np.cos(angle), outer_radius * np.sin(angle)
        ax.plot([x_start, x_end], [y_start, y_end],
                linestyle='--',
                color='black',
                linewidth=1.0)

    # Draw outer circle
    from matplotlib.patches import Circle
    circle = Circle((0, 0), outer_radius,
                   fill=False,
                   linestyle='-',
                   color='black',
                   linewidth=1.0)
    ax.add_patch(circle)

    # Set aspect ratio and limits
    ax.set_aspect('equal')
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.axis('off')

    # Set fixed boundaries to ensure exact 500x500 pixels
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save PNG image
    png_filename = 'sector_grid_a_pilot.png'
    png_path = os.path.join(output_folder, png_filename)

    plt.savefig(png_path, dpi=dpi, pad_inches=0, transparent=True)
    plt.close()

    print(f'Saved {png_filename}')
    print(f'Image size: {figsize[0]*dpi} x {figsize[1]*dpi} pixels')