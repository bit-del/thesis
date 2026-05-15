"""Run colour correction from cli."""

from typing import Optional
import argparse

from openflexure_colour_correction import unmix_dir


def main(argv: Optional[list[str]] = None) -> None:
    """Parse args and unmix all images in the input directory."""
    parser = argparse.ArgumentParser(description="Colour correct a directory of images")

    parser.add_argument("directory", help="The directory containing images to correct.")

    args = parser.parse_args(argv)

    unmix_dir(args.directory)


if __name__ == "__main__":
    main()
