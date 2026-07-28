#!/usr/bin/env python3
"""
02_generate_noise.py

Generate a low-contrast Gaussian noise background of size 1080x720.

Outputs:
  - stimuli/noise_gaussian_1080x720.png
Optionally also outputs:
  - stimuli/noise_gaussian_1080x720.npy  (float array, normalized 0..1)

Notes:
- "Low contrast" is achieved by using a small noise standard deviation.
- The image is saved as 8-bit grayscale (PNG).
- You can easily adapt to RGB if needed.
"""
import os
import numpy as np
from PIL import Image


def main():
    # Target resolution
    image_width_pixels = 1080
    image_height_pixels = 720

    # Output paths
    output_directory = "stimuli"
    os.makedirs(output_directory, exist_ok=True)

    filename_stem = f"noise_gaussian_{image_width_pixels}x{image_height_pixels}"
    png_output_path = os.path.join(output_directory, f"{filename_stem}.png")
    array_output_path = os.path.join(output_directory, f"{filename_stem}.npy")

    # Base luminance and noise strength (low contrast)
    # We generate noise as: image = mean + std * N(0,1)
    mean_luminance = 0.5
    noise_std = 0.12    # low contrast; tweak: 0.03 (very subtle) to 0.12 (noticeable)

    # Create Gaussian noise
    gaussian_noise = np.random.normal(
        loc=0.0,
        scale=noise_std,
        size=(image_height_pixels, image_width_pixels),
    ).astype(np.float32)
    normalized_luminance = (mean_luminance + gaussian_noise).clip(0.0, 1.0)

    # Save PNG as 8-bit grayscale
    grayscale_pixels = (normalized_luminance * 255.0).round().astype(np.uint8)
    grayscale_image = Image.fromarray(grayscale_pixels, mode="L")
    grayscale_image.save(png_output_path)

    # Save numpy array (normalized float) for reproducibility / later use
    np.save(array_output_path, normalized_luminance)

    print(f"Saved: {png_output_path}")
    print(f"Saved: {array_output_path}")
    print(
        "Stats (normalized): "
        f"min={normalized_luminance.min():.4f}, "
        f"max={normalized_luminance.max():.4f}, "
        f"mean={normalized_luminance.mean():.4f}, "
        f"std={normalized_luminance.std():.4f}"
    )


if __name__ == "__main__":
    main()
