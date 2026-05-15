#! /usr/bin/env python3
"""A script to generate the default tensor from the calibration data."""

import os

import numpy as np
import openflexure_colour_correction as occ

THIS_DIR = os.path.dirname(__file__)


def main():
    """Generate the unmix_tensor.npy from the neopixel_jig calibration data."""
    cal_dir = os.path.join(THIS_DIR, "calibration_data", "neopixel_jig")
    cal_dir = os.path.normpath(cal_dir)

    unmix_tensor = occ.calculate_unmix_tensor(cal_dir)

    out_dir = os.path.join(THIS_DIR, "openflexure_colour_correction", "data")
    out_file = os.path.join(out_dir, "unmix_tensor.npy")

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    np.save(out_file, unmix_tensor)


if __name__ == "__main__":
    main()
