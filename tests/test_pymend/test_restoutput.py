"""Integration tests of output to numpy format."""

import pymend.docstring_parser as dsp
from pymend.docstring_info import FixerSettings

from .util import check_expected_diff


def test_blank_lines() -> None:
    """Test that blank lines are set correctly."""
    check_expected_diff(
        "blank_lines",
        output_style=dsp.DocstringStyle.REST,
        fixer_settings=FixerSettings(force_params=False),
    )
