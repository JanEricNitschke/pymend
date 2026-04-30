"""Integration tests of output to numpy format."""

import pymend.docstring_parser as dsp
from pymend.docstring_info import FixerSettings

from .util import check_expected_diff


def test_blank_lines() -> None:
    """Test that blank lines are set correctly."""
    check_expected_diff(
        "blank_lines",
        output_style=dsp.DocstringStyle.EPYDOC,
        fixer_settings=FixerSettings(force_params=False),
    )


def test_blank_lines_at_end_of_multiline_docs() -> None:
    """Test that a blank line is inserted at the end of a multiline docstring."""
    check_expected_diff(
        "blank_lines",
        output_style=dsp.DocstringStyle.EPYDOC,
        fixer_settings=FixerSettings(
            force_params=False,
            force_multiline_docs_end_with_blank=True,
        ),
        reference_name="blank_lines_force_multiline_blank",
    )
