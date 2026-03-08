"""Shared test utilities for pymend tests."""

import os
import re
from pathlib import Path

import pytest

import pymend.docstring_parser as dsp
import pymend.pymend as pym
from pymend.docstring_info import FixerSettings

CURRENT_DIR = Path(__file__).parent
UPDATE_EXPECTED = os.environ.get("PYMEND_UPDATE_EXPECTED") == "1"


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


def check_expected_diff(
    test_name: str,
    *,
    output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
    fixer_settings: FixerSettings | None = None,
    reference_name: str | None = None,
) -> None:
    """Check that the patch on source_file equals the expected patch."""
    style_name = output_style.name.lower()
    expected_file = f"{reference_name or test_name}.py.patch.{style_name}.expected"
    if fixer_settings is None:
        fixer_settings = FixerSettings()
    comment = pym.PyComment(
        absdir(f"refs/{test_name}.py"),
        output_style=output_style,
        fixer_settings=fixer_settings,
    )
    if UPDATE_EXPECTED:
        content = "".join(comment._get_patch_lines())
        absdir(f"refs/{expected_file}").write_text(content, encoding="utf-8")
        return
    result = "".join(comment._docstring_diff())
    expected = get_expected_patch(expected_file)
    assert remove_diff_header(result) == remove_diff_header(expected)
