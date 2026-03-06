"""Shared test utilities for pymend tests."""

import re
from pathlib import Path

import pytest

CURRENT_DIR = Path(__file__).parent


def absdir(file: str) -> Path:
    """Get absolute path for file relative to the test directory.

    Parameters
    ----------
    file : str
        File path

    Returns
    -------
    Path
        Absolute path to file
    """
    return CURRENT_DIR / Path(file)


def get_expected_patch(name: str) -> str:
    """Open a patch file, and if found Pymend signature remove the 2 first lines.

    Parameters
    ----------
    name : str
        Name of the patch

    Returns
    -------
    str
        Expected patch as a string.
    """
    try:
        with absdir(f"refs/{name}").open(encoding="utf-8") as file:
            expected_lines = file.readlines()
            if expected_lines[0].startswith("# Patch"):
                expected_lines = expected_lines[2:]
            expected = "".join(expected_lines)
    except Exception as error:  # noqa: BLE001
        pytest.fail(f'Raised exception: "{error}"')
    return expected


def remove_diff_header(diff: str) -> str:
    """Remove header differences from diff.

    Parameters
    ----------
    diff : str
        Diff file to clean.

    Returns
    -------
    str
        Cleaned diff.
    """
    return re.sub(r"(@@.+@@)|(\-\-\-.*)|(\+\+\+.*)", "", diff)
