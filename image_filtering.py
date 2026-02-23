"""
CS 4391 - Intro to Computer Vision
Assignment 2 – Image Filtering
Spring 2026

Implements the following filters from scratch (no OpenCV filter functions):
  a. 7x7 Box Blur
  b. 15x15 Gaussian Blur
  c. 15x15 Motion Blur
  d. 3x3 Laplacian Sharpening
  e. Canny Edge Detection
"""

import numpy as np
import cv2
import os
import math

# ─── Configuration ────────────────────────────────────────────────────────────
INPUT_IMAGE_PATH = "lena_512.jpg"  # <-- Change this to your input image filename
OUTPUT_DIR = "output"

# ─── Helper: Generic 2D Convolution ──────────────────────────────────────────

def convolve2d(image, kernel):
    """
    Apply a 2D convolution (correlation) of *kernel* over *image*.
    Handles both grayscale and colour (BGR) images.
    Uses zero-padding so the output is the same size as the input.

    Parameters
    ----------
    image : np.ndarray
        Input image (H x W) or (H x W x C), dtype uint8 or float.
    kernel : np.ndarray
        2D kernel of shape (kH x kW).

    Returns
    -------
    np.ndarray
        Filtered image, same shape as input, dtype float64.
    """
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2

    if image.ndim == 2:
        # Grayscale
        h, w = image.shape
        padded = np.pad(image.astype(np.float64), ((pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        output = np.zeros((h, w), dtype=np.float64)
        for i in range(h):
            for j in range(w):
                region = padded[i:i + kh, j:j + kw]
                output[i, j] = np.sum(region * kernel)
        return output
    else:
        # Colour – filter each channel independently
        h, w, c = image.shape
        output = np.zeros_like(image, dtype=np.float64)
        for ch in range(c):
            output[:, :, ch] = convolve2d(image[:, :, ch], kernel)
        return output


# ═══════════════════════════════════════════════════════════════════════════════
# (a) 7 × 7 Box Blur
# ═══════════════════════════════════════════════════════════════════════════════

def box_blur(image, size=7):
    """
    Apply a *size* × *size* box (mean) blur to *image*.

    Parameters
    ----------
    image : np.ndarray
    size  : int – kernel side length (default 7).

    Returns
    -------
    np.ndarray (uint8)
    """
    # TODO: Build the box blur kernel (uniform weights summing to 1)
    kernel = np.ones((size, size), dtype=np.float64) / (size * size)

    # TODO: Convolve and clip to uint8
    result = convolve2d(image, kernel)
    return np.clip(result, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# (b) 15 × 15 Gaussian Blur
# ═══════════════════════════════════════════════════════════════════════════════

def gaussian_blur(image, kernel_size=15, sigma=4.0):
    """
    Apply a Gaussian blur to *image*.

    The 2D Gaussian kernel is generated using cv2.getGaussianKernel (allowed
    per the assignment instructions).

    Parameters
    ----------
    image       : np.ndarray
    kernel_size : int   – must be odd (default 15).
    sigma       : float – standard deviation (default 4.0).

    Returns
    -------
    np.ndarray (uint8)
    """
    # Generate 2D Gaussian kernel (this usage of OpenCV is allowed)
    kernel1d = cv2.getGaussianKernel(kernel_size, sigma)
    kernel2d = np.outer(kernel1d, kernel1d)

    # TODO: Convolve and clip to uint8
    result = convolve2d(image, kernel2d)
    return np.clip(result, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# (c) 15 × 15 Motion Blur
# ═══════════════════════════════════════════════════════════════════════════════

def motion_blur(image, size=15):
    """
    Apply a diagonal motion blur to *image*.

    Parameters
    ----------
    image : np.ndarray
    size  : int – kernel size (default 15).

    Returns
    -------
    np.ndarray (uint8)
    """
    # Build diagonal motion-blur kernel
    kernel = np.zeros((size, size), dtype=np.float64)
    np.fill_diagonal(kernel, 1)
    kernel = kernel / size

    # TODO: Convolve and clip to uint8
    result = convolve2d(image, kernel)
    return np.clip(result, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# (d) 3 × 3 Laplacian Sharpening
# ═══════════════════════════════════════════════════════════════════════════════

def laplacian_sharpen(image):
    """
    Apply the Laplacian sharpening kernel to *image*.

    Kernel:
        [[-1, -1, -1],
         [-1,  9, -1],
         [-1, -1, -1]]

    Returns
    -------
    np.ndarray (uint8)
    """
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]], dtype=np.float64)

    # TODO: Convolve and clip to uint8
    result = convolve2d(image, kernel)
    return np.clip(result, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# (e) Canny Edge Detection  (from scratch)
# ═══════════════════════════════════════════════════════════════════════════════

def canny_edge_detection(image, low_threshold=50, high_threshold=150):
    """
    Canny edge detection implemented from scratch.

    Steps
    -----
    1. Convert to grayscale (if needed).
    2. Smooth with a 5 × 5 Gaussian filter.
    3. Compute gradient magnitude & direction using Sobel kernels.
    4. Non-maximum suppression.
    5. Double-threshold & edge tracking by hysteresis.

    Parameters
    ----------
    image          : np.ndarray – input image (BGR or grayscale).
    low_threshold  : int
    high_threshold : int

    Returns
    -------
    np.ndarray (uint8) – binary edge map (0 or 255).
    """

    # ── Step 0: Convert to grayscale ─────────────────────────────────────
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    else:
        gray = image.astype(np.float64)

    # ── Step 1: 5 × 5 Gaussian smoothing ─────────────────────────────────
    # TODO: Generate a 5×5 Gaussian kernel and convolve
    gauss_kernel1d = cv2.getGaussianKernel(5, 1.0)
    gauss_kernel2d = np.outer(gauss_kernel1d, gauss_kernel1d)
    smoothed = convolve2d(gray, gauss_kernel2d)

    # ── Step 2: Sobel gradients ───────────────────────────────────────────
    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1],
                        [-2, 0, 2],
                        [-1, 0, 1]], dtype=np.float64)

    sobel_y = np.array([[-1, -2, -1],
                        [ 0,  0,  0],
                        [ 1,  2,  1]], dtype=np.float64)

    # TODO: Compute gradients Gx and Gy
    gx = convolve2d(smoothed, sobel_x)
    gy = convolve2d(smoothed, sobel_y)

    # TODO: Compute gradient magnitude and direction
    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    direction = np.arctan2(gy, gx)  # radians

    # ── Step 3: Non-maximum suppression ───────────────────────────────────
    # TODO: For each pixel, check if its magnitude is a local maximum
    #       in the gradient direction. If not, suppress (set to 0).
    nms = _non_max_suppression(magnitude, direction)

    # ── Step 4: Double threshold & hysteresis ─────────────────────────────
    # TODO: Classify pixels as strong, weak, or suppressed.
    #       Then trace edges: weak pixels connected to strong pixels
    #       become strong; the rest are suppressed.
    edges = _hysteresis_thresholding(nms, low_threshold, high_threshold)

    return edges.astype(np.uint8)


def _non_max_suppression(magnitude, direction):
    """
    Thin edges by keeping only local maxima along the gradient direction.

    Parameters
    ----------
    magnitude : np.ndarray (H x W) – gradient magnitudes.
    direction : np.ndarray (H x W) – gradient angles in radians.

    Returns
    -------
    np.ndarray (H x W) – thinned magnitude map.
    """
    h, w = magnitude.shape
    output = np.zeros((h, w), dtype=np.float64)

    # Convert angles to degrees [0, 180)
    angle = np.rad2deg(direction) % 180

    for i in range(1, h - 1):
        for j in range(1, w - 1):
            # TODO: Determine the two neighbours to compare based on
            #       the quantised gradient direction (0°, 45°, 90°, 135°).
            q, r = 0.0, 0.0  # neighbours along gradient direction

            # 0° (horizontal edge → compare left/right)
            if (0 <= angle[i, j] < 22.5) or (157.5 <= angle[i, j] <= 180):
                q = magnitude[i, j + 1]
                r = magnitude[i, j - 1]
            # 45°
            elif 22.5 <= angle[i, j] < 67.5:
                q = magnitude[i + 1, j - 1]
                r = magnitude[i - 1, j + 1]
            # 90° (vertical edge → compare top/bottom)
            elif 67.5 <= angle[i, j] < 112.5:
                q = magnitude[i + 1, j]
                r = magnitude[i - 1, j]
            # 135°
            elif 112.5 <= angle[i, j] < 157.5:
                q = magnitude[i - 1, j - 1]
                r = magnitude[i + 1, j + 1]

            # Keep pixel only if it is the local maximum
            if magnitude[i, j] >= q and magnitude[i, j] >= r:
                output[i, j] = magnitude[i, j]
            else:
                output[i, j] = 0

    return output


def _hysteresis_thresholding(nms, low, high):
    """
    Apply double thresholding and edge tracking by hysteresis.

    Parameters
    ----------
    nms  : np.ndarray – non-max-suppressed magnitude map.
    low  : float      – low threshold.
    high : float      – high threshold.

    Returns
    -------
    np.ndarray (uint8) – final binary edge map (0 or 255).
    """
    h, w = nms.shape
    result = np.zeros((h, w), dtype=np.uint8)

    strong = 255
    weak = 75

    # Classify pixels
    strong_i, strong_j = np.where(nms >= high)
    weak_i, weak_j = np.where((nms >= low) & (nms < high))

    result[strong_i, strong_j] = strong
    result[weak_i, weak_j] = weak

    # TODO: Edge tracking – promote weak pixels connected to strong pixels
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            if result[i, j] == weak:
                # Check 8-connected neighbourhood for a strong pixel
                if (result[i - 1, j - 1] == strong or result[i - 1, j] == strong or
                    result[i - 1, j + 1] == strong or result[i, j - 1] == strong or
                    result[i, j + 1] == strong or result[i + 1, j - 1] == strong or
                    result[i + 1, j] == strong or result[i + 1, j + 1] == strong):
                    result[i, j] = strong
                else:
                    result[i, j] = 0

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Main driver
# ═══════════════════════════════════════════════════════════════════════════════

def save(name, image):
    """Save *image* to OUTPUT_DIR with the given *name*."""
    path = os.path.join(OUTPUT_DIR, name)
    cv2.imwrite(path, image)
    print(f"  Saved → {path}")


def main():
    # Load input image
    image = cv2.imread(INPUT_IMAGE_PATH)
    if image is None:
        print(f"ERROR: Could not load image at '{INPUT_IMAGE_PATH}'.")
        print("       Place your input image in the project folder and update INPUT_IMAGE_PATH.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Input image loaded: {INPUT_IMAGE_PATH}  (shape={image.shape})\n")

    # (a) Box Blur
    print("[a] Applying 7×7 Box Blur …")
    result_a = box_blur(image, size=7)
    save("a_box_blur_7x7.png", result_a)

    # (b) Gaussian Blur
    print("[b] Applying 15×15 Gaussian Blur (σ=4.0) …")
    result_b = gaussian_blur(image, kernel_size=15, sigma=4.0)
    save("b_gaussian_blur_15x15.png", result_b)

    # (c) Motion Blur
    print("[c] Applying 15×15 Motion Blur …")
    result_c = motion_blur(image, size=15)
    save("c_motion_blur_15x15.png", result_c)

    # (d) Laplacian Sharpening
    print("[d] Applying 3×3 Laplacian Sharpening …")
    result_d = laplacian_sharpen(image)
    save("d_laplacian_sharpen.png", result_d)

    # (e) Canny Edge Detection
    print("[e] Running Canny Edge Detection …")
    result_e = canny_edge_detection(image, low_threshold=50, high_threshold=150)
    save("e_canny_edges.png", result_e)

    print("\nAll filters applied. Results saved in '{}'.".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()
