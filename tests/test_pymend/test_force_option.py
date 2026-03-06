"""Integration tests for ForceOption modes (force, unforce, noforce)."""

import pytest

import pymend.pymend as pym
from pymend.docstring_info import FixerSettings, ForceOption

from .util import absdir, get_expected_patch, remove_diff_header


@pytest.mark.parametrize("mode", list(ForceOption))
def test_force_option(mode: ForceOption) -> None:
    """Check that the patch for force_option.py matches expected for each mode."""
    expected = get_expected_patch(
        f"force_option.py.patch.{mode.value}.numpydoc.expected"
    )
    settings = FixerSettings(
        force_arg_types=mode,
        force_return_type=mode,
        force_attribute_types=mode,
    )
    comment = pym.PyComment(absdir("refs/force_option.py"), fixer_settings=settings)
    result = "".join(comment._docstring_diff())
    assert remove_diff_header(result) == remove_diff_header(expected)
