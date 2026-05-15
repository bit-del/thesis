"""Functions for raw image loading and creating unmixing tensors."""

import os

import numpy as np
from scipy import ndimage
from PIL import Image

# Import some code extracted from the `picamera` library and modified
# to work independently
from .external import picamera_array


full_resolution = (3280, 2464)


class DummyCam(object):
    """A dummy PiCamera-like object that to allow reading of raw images.

    Note: this will only work for version 2 of the camera at present.
    """

    resolution = full_resolution
    revision = "IMX219"
    sensor_mode = 0


def load_raw_image(filename, array_type=picamera_array.PiSharpBayerArray, open_jpeg=False):
    """Load the raw image data (and optionally the processed image data and EXIF metadata) from a file."""
    with open(filename, mode="rb") as file:
        jpeg = file.read()
    cam = DummyCam()
    bayer_array = array_type(cam)
    bayer_array.write(jpeg)
    bayer_array.flush()

    if open_jpeg:
        jpeg = Image.open(filename)
        # with thanks to https://stackoverflow.com/questions/4764932/in-python-how-do-i-read-the-exif-data-for-an-image
        exif_data = jpeg._getexif()
        return bayer_array, jpeg, exif_data
    return bayer_array


def bin_image(image, b=2):
    """Bin bxb squares of an image together."""
    w, h = image.shape[:2]
    new_shape = (w // b, b, h // b, b)
    if len(image.shape) > 2:
        new_shape += image.shape[2:]
    if w % b != 0 or h % b != 0:
        print("Warning: pixels are being dropped from the binned image!")
        image = image[: w - (w % b), : h - (h % b), ...]
    return image.reshape(new_shape).mean(axis=1).mean(axis=2)


def load_raw_image_and_bin(filename):
    """Load an image from the raw data in a jpeg file, and return a binned version."""
    pi_bayer_array = load_raw_image(filename)
    image = (
        pi_bayer_array.array - np.array([16, 32, 16])[np.newaxis, np.newaxis, :]
    )  # correct for the zero offset in the raw data
    return bin_image(image, 16)


def load_run(calibration_dir, illuminations):
    """Load the R,G,B,W calibration images and any additional images."""
    output = {}
    for k, rgb in illuminations.items():
        output[k] = load_raw_image_and_bin(
            os.path.join(calibration_dir, "capture_r{}_g{}_b{}.jpg".format(*rgb))
        )
    for f in os.listdir(calibration_dir):
        if f.startswith("additional_image_"):
            output[f[17:-4]] = load_raw_image_and_bin(os.path.join(calibration_dir, f))
    return output


def crosstalk_matrices(run):
    """Construct a 4d array of colour crosstalk information.

    This function returns a 3x3 matrix at each pixel of the calibration images.
    Inverting this matrix
    """
    return np.stack([run[k] for k in ["R", "G", "B"]], axis=3) / run["W"][:, :, :, np.newaxis]


def central_colour(image):
    """Find the colour of the central portion of an image."""
    w, h = image.shape[:2]
    return np.mean(
        np.mean(
            image[w * 4 // 9 : w // 2 + w * 5 // 9, h * 4 // 9 : h * 5 // 9, ...],
            axis=0,
        ),
        axis=0,
    )


def colour_unmixing_matrices(cal, colour_target="rgb", smoothing=None):
    """Return a matrix that turns the camera's recorded colour back into "perfect" colour.

    cal should be a calibration run (dictionary) with, as a minimum, W, R, G, and B images.

    :param cal: a dictionary with (at least) R, G, B, and W images
    :param colour_target: "rgb" (default) or "centre".  "rgb" will unmix to fully saturated colours,
        while "centre" will unmix so the edges of the image match the centre of the image.
    :param smoothing: None (default) for no smoothing, or a number (in pixels) to apply a Gaussian
        blur to the compensation matrices.

    :returns: an NxMx3x3 unmixing matrix
    """
    crosstalk = crosstalk_matrices(cal)
    compensation_matrices = np.empty_like(crosstalk)
    # Doing this with a massive for loop is inefficient, but easy to read!
    for i in range(crosstalk.shape[0]):
        for j in range(crosstalk.shape[1]):
            compensation_matrices[i, j, :, :] = np.linalg.inv(crosstalk[i, j, :, :])
    if colour_target in {"centre", "center"}:
        central_response = np.array([central_colour(cal[k] / cal["W"]) for k in ["R", "G", "B"]])
        print("Adding up the R/G/B images, we get:", np.sum(central_response, axis=0))
        compensation_matrices = np.sum(
            compensation_matrices[:, :, :, np.newaxis, :]
            * central_response[np.newaxis, np.newaxis, :, :, np.newaxis],
            axis=-3,
        )
    if smoothing is not None:
        compensation_matrices = ndimage.gaussian_filter(
            compensation_matrices, (smoothing, smoothing, 0, 0), order=0
        )
    return compensation_matrices


def calculate_unmix_tensor(calibration_dir):
    """Calculate the unmix tensor given the images in the input directory."""
    # The neopixel data gives the flattest colour

    illuminations = {
        "W": (255, 255, 255),
        "R": (255, 0, 0),
        "G": (0, 255, 0),
        "B": (0, 0, 255),
        "K": (0, 0, 0),
    }
    # Load the images taken with solid colour (White, Red, Green, Blue, and Black)
    data = load_run(calibration_dir, illuminations)

    return colour_unmixing_matrices(data, colour_target="centre", smoothing=3)
