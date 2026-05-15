# openflexure-colour-correction

This repository is for developing colour correction algorithms for the OpenFlexure Microscope.

It is based of data and algorithms from [our 2018 paper](https://doi.org/10.5334/joh.20) and the associated [repository](https://gitlab.com/bath_open_instrumentation_group/picamera_cra_compensation). 

# Install

To install clone this repository and run:

    pip install .

# Generate default unmixing tensor

Before colour correction can be applied a default unmixing tensor needs to be generated from the calibration

From the main directory run the `generate_default_tensor.py` script.

# Correct the images in a directory

Once the default unmixing tensor has been created, you can run the following command to correct the colour of the images in a directory:

    openflexure-colour-correction <path-to-directory>

changing `<path-to-directory>` as appropriate. This will create a new folder in the directory, so your original images won't be overwritten.
