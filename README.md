# CS 4391 – Assignment 2: Image Filtering

## Setup

```bash
pip install numpy opencv-python
```

## Usage

1. Place your input image in the project root and name it `input.png` (or edit `INPUT_IMAGE_PATH` at the top of `image_filtering.py`).
2. Run:

```bash
python image_filtering.py
```

3. Results will be saved in the `output/` folder.

## Filters Implemented

| # | Filter | Output File |
|---|--------|-------------|
| a | 7×7 Box Blur | `a_box_blur_7x7.png` |
| b | 15×15 Gaussian Blur (σ=4.0) | `b_gaussian_blur_15x15.png` |
| c | 15×15 Diagonal Motion Blur | `c_motion_blur_15x15.png` |
| d | 3×3 Laplacian Sharpening | `d_laplacian_sharpen.png` |
| e | Canny Edge Detection | `e_canny_edges.png` |