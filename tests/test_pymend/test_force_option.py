"""Integration tests for ForceOption modes (force, unforce, noforce)."""

import pytest

import pymend.pymend as pym
from pymend.docstring_info import FixerSettings, ForceOption

from .util import absdir, get_expected_patch, remove_diff_header


def test_force_option_numpydoc() -> None:
    """Check that the patch for force_option.py matches expected for FORCE mode.

    UNFORCE and NOFORCE are rejected for numpydoc (tested separately).
    """
    expected = get_expected_patch("force_option.py.patch.force.numpydoc.expected")
    settings = FixerSettings(
        force_arg_types=ForceOption.FORCE,
        force_return_type=ForceOption.FORCE,
        force_attribute_types=ForceOption.FORCE,
    )
    comment = pym.PyComment(absdir("refs/force_option.py"), fixer_settings=settings)
    result = "".join(comment._docstring_diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def test_force_option_numpydoc_rejects_non_force_return() -> None:
    """NumPy output style requires force_return_type=FORCE."""
    for mode in (ForceOption.NOFORCE, ForceOption.UNFORCE):
        settings = FixerSettings(
            force_arg_types=mode,
            force_return_type=mode,
            force_attribute_types=mode,
        )
        with pytest.raises(ValueError, match="NumPy docstring style requires"):
            pym.PyComment(absdir("refs/force_option.py"), fixer_settings=settings)
