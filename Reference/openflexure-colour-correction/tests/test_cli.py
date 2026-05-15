"""Tests for the colour correction CLI."""

import sys
import tempfile

import pytest

from openflexure_colour_correction import __main__ as ofcc_main


@pytest.fixture
def tempdir():
    """Fixture that yields a temporary directory path as a string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_main_calls_unmix_dir_with_directory(tempdir, mocker):
    """Ensure main() calls unmix_dir with the provided directory argument."""
    mock_unmix = mocker.patch.object(ofcc_main, "unmix_dir")
    ofcc_main.main([tempdir])
    assert mock_unmix.call_count == 1
    assert mock_unmix.call_args.args[0] == tempdir


def test_main_errors_with_no_directory(capsys):
    """Ensure main() calls unmix_dir with the provided directory argument."""
    # with pytest.raises(SystemExit, match="the following arguments are required"):
    with pytest.raises(SystemExit) as excinfo:
        ofcc_main.main()
    assert excinfo.value.code == 2

    # Check the error message on stderr
    captured = capsys.readouterr()
    assert "the following arguments are required: directory" in captured.err


def test_main_uses_sys_argv_by_default(tempdir, mocker):
    """Ensure main() defaults to sys.argv when no args are provided."""
    mocker.patch.object(sys, "argv", ["progname", tempdir])
    mock_unmix = mocker.patch.object(ofcc_main, "unmix_dir")

    ofcc_main.main()

    assert mock_unmix.call_count == 1
    assert mock_unmix.call_args.args[0] == tempdir
