#!/usr/bin/env python3
"""
02_generate_noise.py

Generate a low-contrast Gaussian noise background of size 1920x1080.

Outputs:
  - stimuli/noise_gaussian_1920x1080.png
Optionally also outputs:
  - stimuli/noise_gaussian_1920x1080.npy  (float array, normalized 0..1)

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
    width = 1080
    height = 720

    # Output paths
    output_dir = "stimuli"
    os.makedirs(output_dir, exist_ok=True)

    out_png = os.path.join(output_dir, f"noise_gaussian_{width}x{height}.png")
    out_npy = os.path.join(output_dir, f"noise_gaussian_{width}x{height}.npy")

    # Base luminance and noise strength (low contrast)
    # We generate noise as: image = mean + std * N(0,1)
    mean = 0.5          # mid-gray in normalized 0..1
    noise_std = 0.12    # low contrast; tweak: 0.03 (very subtle) to 0.12 (noticeable)

    # Create Gaussian noise
    noise = np.random.normal(loc=0.0, scale=noise_std, size=(height, width)).astype(np.float32)
    img = (mean + noise).clip(0.0, 1.0)

    # Save PNG as 8-bit grayscale
    img_u8 = (img * 255.0).round().astype(np.uint8)
    im = Image.fromarray(img_u8, mode="L")
    im.save(out_png)

    # Save numpy array (normalized float) for reproducibility / later use
    np.save(out_npy, img)

    print(f"Saved: {out_png}")
    print(f"Saved: {out_npy}")
    print(f"Stats (normalized): min={img.min():.4f}, max={img.max():.4f}, mean={img.mean():.4f}, std={img.std():.4f}")


if __name__ == "__main__":
    main()