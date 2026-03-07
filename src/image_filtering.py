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

import numpy as np  # NumPy for array/matrix operations
import cv2          # OpenCV for image I/O and kernel generation (not used for filtering)
import os            # OS module for file path and directory operations

# ─── Configuration ────────────────────────────────────────────────────────────
# Path to the input image file (change this to match your image filename)
INPUT_IMAGE_PATH = "lena_512.jpg"
# Directory where all output/result images will be saved
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
    # Get the height and width of the kernel
    kh, kw = kernel.shape
    # Calculate how much padding is needed on each side (half the kernel size)
    pad_h, pad_w = kh // 2, kw // 2

    if image.ndim == 2:
        # ── Grayscale image path ──
        # Get the height and width of the input image
        h, w = image.shape
        # Add zero-padding around the image borders so the output stays the same size
        padded = np.pad(image.astype(np.float64), ((pad_h, pad_h), (pad_w, pad_w)), mode='constant')
        # Create an empty output array to store the convolution results
        output = np.zeros((h, w), dtype=np.float64)
        # Slide the kernel over every pixel in the image
        for i in range(h):
            for j in range(w):
                # Extract the region of the image under the kernel
                region = padded[i:i + kh, j:j + kw]
                # Multiply element-wise and sum to get the filtered pixel value
                output[i, j] = np.sum(region * kernel)
        return output
    else:
        # ── Colour image path – filter each channel (B, G, R) independently ──
        h, w, c = image.shape
        # Allocate output array with same shape as the input image
        output = np.zeros_like(image, dtype=np.float64)
        # Apply the convolution to each colour channel separately
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
    # Build the box blur kernel: a matrix of ones divided by the total number
    # of elements so all weights are equal and sum to 1 (uniform average)
    kernel = np.ones((size, size), dtype=np.float64) / (size * size)

    # Apply the kernel to the image using 2D convolution
    result = convolve2d(image, kernel)
    # Clip values to valid pixel range [0, 255] and convert back to uint8
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
    # Generate a 1D Gaussian kernel using OpenCV (allowed per assignment instructions)
    kernel1d = cv2.getGaussianKernel(kernel_size, sigma)
    # Create the 2D Gaussian kernel by computing the outer product of the 1D kernel
    # with itself, producing a symmetric 2D bell-curve-shaped weight matrix
    kernel2d = np.outer(kernel1d, kernel1d)

    # Apply the Gaussian kernel to the image using 2D convolution
    result = convolve2d(image, kernel2d)
    # Clip values to valid pixel range [0, 255] and convert back to uint8
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
    # Create a size×size matrix of zeros for the motion blur kernel
    kernel = np.zeros((size, size), dtype=np.float64)
    # Fill the main diagonal with 1s to create a diagonal motion blur effect
    np.fill_diagonal(kernel, 1)
    # Normalize the kernel so all values sum to 1 (preserves image brightness)
    kernel = kernel / size

    # Apply the diagonal motion blur kernel to the image using 2D convolution
    result = convolve2d(image, kernel)
    # Clip values to valid pixel range [0, 255] and convert back to uint8
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
    # Define the 3×3 Laplacian sharpening kernel as specified in the assignment.
    # The center value of 9 enhances the current pixel while subtracting the
    # surrounding neighbours, which sharpens edges and fine detail.
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]], dtype=np.float64)

    # Apply the sharpening kernel to the image using 2D convolution
    result = convolve2d(image, kernel)
    # Clip values to valid pixel range [0, 255] and convert back to uint8
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
    # Canny operates on a single-channel image, so convert colour to gray
    if image.ndim == 3:
        # Convert BGR colour image to grayscale and store as float for precision
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    else:
        # Image is already grayscale; just cast to float64
        gray = image.astype(np.float64)

    # ── Step 1 (i): 5 × 5 Gaussian smoothing ─────────────────────────────
    # Smooth the image first to reduce noise before edge detection
    # Generate a 1D Gaussian kernel with size 5 and sigma 1.0
    gauss_kernel1d = cv2.getGaussianKernel(5, 1.0)
    # Create the 2D Gaussian kernel via outer product of the 1D kernel
    gauss_kernel2d = np.outer(gauss_kernel1d, gauss_kernel1d)
    # Convolve the grayscale image with the 5×5 Gaussian to smooth it
    smoothed = convolve2d(gray, gauss_kernel2d)

    # ── Step 2 (ii): Sobel gradients ──────────────────────────────────────
    # Define the Sobel kernel for detecting horizontal (x-direction) edges
    sobel_x = np.array([[-1, 0, 1],
                        [-2, 0, 2],
                        [-1, 0, 1]], dtype=np.float64)

    # Define the Sobel kernel for detecting vertical (y-direction) edges
    sobel_y = np.array([[-1, -2, -1],
                        [ 0,  0,  0],
                        [ 1,  2,  1]], dtype=np.float64)

    # Compute the horizontal gradient (Gx) by convolving with sobel_x
    gx = convolve2d(smoothed, sobel_x)
    # Compute the vertical gradient (Gy) by convolving with sobel_y
    gy = convolve2d(smoothed, sobel_y)

    # Compute gradient magnitude: sqrt(Gx^2 + Gy^2) at each pixel
    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    # Compute gradient direction (angle in radians) at each pixel
    direction = np.arctan2(gy, gx)

    # ── Step 3 (iii): Non-maximum suppression ─────────────────────────────
    # Thin the edges by keeping only pixels that are local maxima
    # along their gradient direction; all others are suppressed to 0
    nms = _non_max_suppression(magnitude, direction)

    # ── Step 4 (iv): Double threshold & hysteresis ────────────────────────
    # Classify edge pixels as strong or weak based on two thresholds,
    # then promote weak pixels that are connected to strong pixels
    edges = _hysteresis_thresholding(nms, low_threshold, high_threshold)

    # Return the final binary edge map as uint8 (values are 0 or 255)
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
    # Get image dimensions
    h, w = magnitude.shape
    # Create output array initialized to zero (suppressed by default)
    output = np.zeros((h, w), dtype=np.float64)

    # Convert gradient angles from radians to degrees, mapped to [0, 180)
    # so we can quantise them into four directional bins
    angle = np.rad2deg(direction) % 180

    # Loop over every interior pixel (skip 1-pixel border to avoid out-of-bounds)
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            # q and r will hold the magnitudes of the two neighbours
            # along the gradient direction for comparison
            q, r = 0.0, 0.0

            # 0° direction: gradient is roughly horizontal,
            # so compare with the left and right neighbours
            if (0 <= angle[i, j] < 22.5) or (157.5 <= angle[i, j] <= 180):
                q = magnitude[i, j + 1]  # right neighbour
                r = magnitude[i, j - 1]  # left neighbour
            # 45° direction: gradient is along the diagonal,
            # so compare with bottom-left and top-right neighbours
            elif 22.5 <= angle[i, j] < 67.5:
                q = magnitude[i + 1, j - 1]  # bottom-left neighbour
                r = magnitude[i - 1, j + 1]  # top-right neighbour
            # 90° direction: gradient is roughly vertical,
            # so compare with the top and bottom neighbours
            elif 67.5 <= angle[i, j] < 112.5:
                q = magnitude[i + 1, j]  # bottom neighbour
                r = magnitude[i - 1, j]  # top neighbour
            # 135° direction: gradient is along the other diagonal,
            # so compare with top-left and bottom-right neighbours
            elif 112.5 <= angle[i, j] < 157.5:
                q = magnitude[i - 1, j - 1]  # top-left neighbour
                r = magnitude[i + 1, j + 1]  # bottom-right neighbour

            # Keep the pixel only if its magnitude is >= both neighbours
            # (i.e., it is a local maximum along the gradient direction)
            if magnitude[i, j] >= q and magnitude[i, j] >= r:
                output[i, j] = magnitude[i, j]
            else:
                # Suppress (set to zero) if not a local maximum
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
    # Get the image dimensions from the non-max-suppressed magnitude map
    h, w = nms.shape
    # Create an output array initialized to zero (all pixels suppressed)
    result = np.zeros((h, w), dtype=np.uint8)

    # Define intensity values for strong and weak edge pixels
    strong = 255  # definite edge
    weak = 75     # potential edge (needs further analysis)

    # Find all pixel locations where magnitude exceeds the high threshold
    # and mark them as strong edges
    strong_i, strong_j = np.where(nms >= high)
    # Find all pixel locations where magnitude is between low and high
    # and mark them as weak (potential) edges
    weak_i, weak_j = np.where((nms >= low) & (nms < high))

    # Set strong edge pixels to 255 in the result
    result[strong_i, strong_j] = strong
    # Set weak edge pixels to 75 in the result
    result[weak_i, weak_j] = weak

    # Edge tracking by hysteresis: promote weak pixels that are connected
    # to strong pixels. Loop over every interior pixel.
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            if result[i, j] == weak:
                # Check all 8 neighbours around this weak pixel
                # If any neighbour is a strong edge, promote this pixel to strong
                if (result[i - 1, j - 1] == strong or result[i - 1, j] == strong or
                    result[i - 1, j + 1] == strong or result[i, j - 1] == strong or
                    result[i, j + 1] == strong or result[i + 1, j - 1] == strong or
                    result[i + 1, j] == strong or result[i + 1, j + 1] == strong):
                    result[i, j] = strong  # promote weak pixel to strong edge
                else:
                    result[i, j] = 0  # suppress weak pixel with no strong neighbour

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Main driver
# ═══════════════════════════════════════════════════════════════════════════════

def save(name, image):
    """Save the given image to the output directory with the specified filename."""
    # Build the full file path by joining the output directory with the filename
    path = os.path.join(OUTPUT_DIR, name)
    # Write the image to disk using OpenCV's imwrite function
    cv2.imwrite(path, image)
    # Print confirmation message showing where the file was saved
    print(f"  Saved → {path}")


def main():
    """Main driver function. Loads the input image, applies all five filters, and saves results."""

    # Load the input image from disk using OpenCV (reads as BGR colour)
    image = cv2.imread(INPUT_IMAGE_PATH)
    # Check that the image loaded successfully
    if image is None:
        print(f"ERROR: Could not load image at '{INPUT_IMAGE_PATH}'.")
        print("       Place your input image in the project folder and update INPUT_IMAGE_PATH.")
        return

    # Create the output directory if it doesn't already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Print confirmation that the image was loaded along with its dimensions
    print(f"Input image loaded: {INPUT_IMAGE_PATH}  (shape={image.shape})\n")

    # ── (a) Apply the 7×7 box blur filter ──
    print("[a] Applying 7×7 Box Blur …")
    result_a = box_blur(image, size=7)
    save("a_box_blur_7x7.png", result_a)  # save the box-blurred result

    # ── (b) Apply the 15×15 Gaussian blur filter with sigma=4.0 ──
    print("[b] Applying 15×15 Gaussian Blur (σ=4.0) …")
    result_b = gaussian_blur(image, kernel_size=15, sigma=4.0)
    save("b_gaussian_blur_15x15.png", result_b)  # save the Gaussian-blurred result

    # ── (c) Apply the 15×15 diagonal motion blur filter ──
    print("[c] Applying 15×15 Motion Blur …")
    result_c = motion_blur(image, size=15)
    save("c_motion_blur_15x15.png", result_c)  # save the motion-blurred result

    # ── (d) Apply the 3×3 Laplacian sharpening filter ──
    print("[d] Applying 3×3 Laplacian Sharpening …")
    result_d = laplacian_sharpen(image)
    save("d_laplacian_sharpen.png", result_d)  # save the sharpened result

    # ── (e) Apply Canny edge detection ──
    print("[e] Running Canny Edge Detection …")
    result_e = canny_edge_detection(image, low_threshold=50, high_threshold=150)
    save("e_canny_edges.png", result_e)  # save the binary edge map

    # Print final summary message
    print("\nAll filters applied. Results saved in '{}'.".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()
