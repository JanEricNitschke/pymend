"""Integration tests of output to numpy format."""

import pymend.docstring_parser as dsp
import pymend.pymend as pym
from pymend.docstring_info import FixerSettings

from .util import absdir, get_expected_patch, remove_diff_header


def check_expected_diff(
    test_name: str,
    output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
    fixer_settings: FixerSettings | None = None,
) -> None:
    """Check that the patch on source_file equals the expected patch."""
    style_name = output_style.name.lower()
    expected = get_expected_patch(f"{test_name}.py.patch.{style_name}.expected")
    if fixer_settings is None:
        fixer_settings = FixerSettings()
    comment = pym.PyComment(
        absdir(f"refs/{test_name}.py"),
        output_style=output_style,
        fixer_settings=fixer_settings,
    )
    result = "".join(comment._docstring_diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def test_positional_only_identifier() -> None:
    """Make sure that '/' is parsed correctly in signatures."""
    check_expected_diff("positional_only")


def test_keyword_only_identifier() -> None:
    """Make sure that '*' is parsed correctly in signatures."""
    check_expected_diff("keyword_only")


def test_returns() -> None:
    """Make sure single and multi return values are parsed/produced correctly."""
    check_expected_diff("returns")


def test_returns_google() -> None:
    """Make sure multi return values are parsed/produced correctly for Google style."""
    check_expected_diff("returns_google", dsp.DocstringStyle.GOOGLE)


def test_star_args() -> None:
    """Make sure that *args are treated correctly."""
    check_expected_diff("star_args")


def test_starstar_kwargs() -> None:
    """Make sure that **kwargs are treated correctly."""
    check_expected_diff("star_star_kwargs")


def test_module_doc_dot() -> None:
    """Make sure missing '.' are added to the first line of module docstring."""
    check_expected_diff("module_dot_missing")


def test_module_doc_dot_noforce() -> None:
    """Make sure '.' is not added when force_summary_period is False."""
    expected = get_expected_patch("module_dot_noforce.py.patch.numpydoc.expected")
    comment = pym.PyComment(
        absdir("refs/module_dot_missing.py"),
        fixer_settings=FixerSettings(force_summary_period=False),
    )
    result = "".join(comment._docstring_diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def test_ast_ref() -> None:
    """Bunch of different stuff."""
    check_expected_diff("ast_ref")


def test_yields() -> None:
    """Make sure yields are handled correctly from body."""
    check_expected_diff("yields")


def test_raises() -> None:
    """Make sure raises are handled correctly from body."""
    check_expected_diff("raises")


def test_skip_overload() -> None:
    """Function annotated with @overload should be skipped for DS creation."""
    check_expected_diff("skip_overload_decorator")


def test_class_body() -> None:
    """Correctly parse and compose class from body information."""
    check_expected_diff("class_body")


def test_quote_default() -> None:
    """Test that default values of triple quotes do not cause issues."""
    check_expected_diff("quote_default")


def test_blank_lines() -> None:
    """Test that blank lines are set correctly."""
    expected = get_expected_patch("blank_lines.py.patch.numpydoc.expected")
    comment = pym.PyComment(
        absdir("refs/blank_lines.py"),
        fixer_settings=FixerSettings(force_params=False),
    )
    result = "".join(comment._docstring_diff())
    assert remove_diff_header(result) == remove_diff_header(expected)


def test_comments_after_docstring() -> None:
    """Test that comments after the last line are not removed."""
    check_expected_diff("comments_after_docstring")


def test_forward_ref() -> None:
    """Ensure forward reference quotes are stripped from type annotations."""
    check_expected_diff("forward_ref")
