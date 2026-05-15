"""Functions for correcting image colours given an unmixing tensor."""

import os
import re
import json

import numpy as np
import numpy.typing as npt
from PIL import Image
from scipy.ndimage import zoom

# Ignore typing on piexif for now. Need underlying updates or stubs in future
import piexif  # type: ignore

THIS_DIR = os.path.dirname(__file__)


def resize_unmix_tensor(unmix_tensor, shape, half=True):
    """Resize the base unmixing tensor to a new size.

    Optionally disable half-precision logic. This uses more memory.
    """
    t_shape = unmix_tensor.shape
    if shape[0] % t_shape[0] != 0 or shape[1] % t_shape[1] != 0:
        raise ValueError("Input shape is not a multiple of input tensor shape")
    sample_factor = shape[1] // t_shape[1]
    new_unmix_tensor = np.zeros((shape[0], shape[1], 3, 3))
    for i in range(3):
        for j in range(3):
            new_unmix_tensor[:, :, i, j] = zoom(unmix_tensor[:, :, i, j], sample_factor, order=1)
    if half:
        return new_unmix_tensor.astype(np.half)
    return new_unmix_tensor


def unmix_colour(im, unmix_tensor):
    """Unmix the colour of the input image using the unmixing tensor."""
    im_c = np.einsum("ijkl,ijl->ijk", unmix_tensor, im)
    im_c[im_c > 255] = 255
    im_c[im_c < 0] = 0
    return im_c.astype(np.uint8)


def load_2mp_unmix_tensor(npy_path):
    """Load unmixing tensor from numpy object and rescale to 2 megapixels."""
    unmix_tensor = np.load(npy_path)
    return resize_unmix_tensor(unmix_tensor, (1232, 1640), half=False)


def unmix_dir(im_dir):
    """Unmix images in the given directory saving to the directory "color_corr".

    All images must be 2MP
    """
    unmix_tensor_path = os.path.join(THIS_DIR, "data", "unmix_tensor.npy")
    unmix_tensor_2mp = load_2mp_unmix_tensor(unmix_tensor_path)

    out_dir = os.path.join(im_dir, "colour_corr")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    n = 0
    for fname in os.listdir(im_dir):
        # 只要結尾是 png, jpg, jpeg 都接受 (不分大小寫)
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            n += 1
            print(n, fname)
            unmix_img(fname, im_dir, out_dir, unmix_tensor_2mp)


def unmix_img(
    fname: str,
    im_dir: str,
    out_dir: str,
    unmix_tensor_2mp: npt.NDArray,
) -> None:
    """Apply the correction to the given image, and save to disk."""
    im: Image.Image = Image.open(os.path.join(im_dir, fname))
    original_im_format = im.format
    exif_dict = piexif.load(im.info["exif"])
    # Update user comment to say that colour correction was applied
    _update_usercomment(exif_dict)
    im_array = np.array(im)
    im = Image.fromarray(unmix_colour(im_array, unmix_tensor_2mp))
    # If the image is a JPEG, save with optimal, near-lossless settings
    # This test checks the image data itself, not just the filepath
    if original_im_format == "JPEG":
        im.save(
            os.path.join(out_dir, fname),
            exif=piexif.dump(exif_dict),
            quality=95,
            subsampling=0,
        )
    else:
        # Currently, no other format is supported by the OpenFlexure software
        # PNG has been in the past and TIFF may be in the future.
        # PNG is lossless and has no quality settings.
        # TIFF has lots of quality options, in the future if OpenFlexure starts
        # to use TIFF, this may need to be update to not simply use default settings.
        im.save(os.path.join(out_dir, fname), exif=piexif.dump(exif_dict))


def _update_usercomment(exif_dict):
    usercomment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
    user_dict = json.loads(usercomment.decode())
    user_dict["ColourCorrectionApplied"] = True
    usercomment = json.dumps(user_dict).encode()
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = usercomment
