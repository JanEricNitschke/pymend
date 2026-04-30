"""Integration tests of output to numpy format."""

import sys

import pytest

from pymend.docstring_info import FixerSettings, RaisesForceMode

from .util import check_expected_diff


def test_positional_only_identifier() -> None:
    """Make sure that '/' is parsed correctly in signatures."""
    check_expected_diff("positional_only")


def test_keyword_only_identifier() -> None:
    """Make sure that '*' is parsed correctly in signatures."""
    check_expected_diff("keyword_only")


def test_returns() -> None:
    """Make sure single and multi return values are parsed/produced correctly."""
    check_expected_diff("returns")


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
    check_expected_diff(
        "module_dot_missing",
        fixer_settings=FixerSettings(force_summary_period=False),
        reference_name="module_dot_noforce",
    )


def test_ast_ref() -> None:
    """Bunch of different stuff."""
    check_expected_diff("ast_ref")


def test_yields() -> None:
    """Make sure yields are handled correctly from body."""
    check_expected_diff("yields")


def test_raises_modes_off() -> None:
    """Test raises mode OFF - no raises section forced."""
    check_expected_diff(
        "raises_modes",
        fixer_settings=FixerSettings(force_raises=RaisesForceMode.OFF),
        reference_name="raises_modes_off",
    )


def test_raises_modes_per_type() -> None:
    """Test raises mode PER_TYPE - one entry per exception type."""
    check_expected_diff(
        "raises_modes",
        fixer_settings=FixerSettings(force_raises=RaisesForceMode.PER_TYPE),
        reference_name="raises_modes_per_type",
    )


def test_raises_modes_per_site() -> None:
    """Test raises mode PER_SITE - one entry per raise site."""
    check_expected_diff(
        "raises_modes",
        fixer_settings=FixerSettings(force_raises=RaisesForceMode.PER_SITE),
        reference_name="raises_modes_per_site",
    )


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
    check_expected_diff("blank_lines", fixer_settings=FixerSettings(force_params=False))


def test_blank_lines_at_end_of_multiline_docs() -> None:
    """Test that a blank line is inserted at the end of a multiline docstring."""
    check_expected_diff(
        "blank_lines",
        fixer_settings=FixerSettings(
            force_params=False,
            force_multiline_docs_end_with_blank=True,
        ),
        reference_name="blank_lines_force_multiline_blank",
    )


def test_comments_after_docstring() -> None:
    """Test that comments after the last line are not removed."""
    check_expected_diff("comments_after_docstring")


def test_forward_ref() -> None:
    """Ensure forward reference quotes are stripped from type annotations."""
    check_expected_diff("forward_ref")


def test_attribute_classes() -> None:
    """Dataclass/BaseModel fields become attributes; plain classes do not."""
    check_expected_diff("attribute_classes")


def test_init_type_extraction() -> None:
    """__init__ body type extraction for annotated and param-mapped attrs."""
    check_expected_diff(
        "init_type_extraction",
        fixer_settings=FixerSettings(force_attributes=True),
    )


def test_existing_attribute_types() -> None:
    """Wrong/missing types are corrected but missing attributes are not added."""
    check_expected_diff("existing_attribute_types")


def test_existing_attribute_types_force() -> None:
    """With force_attributes, missing attributes are also added."""
    check_expected_diff(
        "existing_attribute_types",
        fixer_settings=FixerSettings(force_attributes=True),
        reference_name="existing_attribute_types_force",
    )


def test_force_summary_blank_line() -> None:
    """Test that blank line after short description is enforced by default."""
    check_expected_diff(
        "force_summary_blank_line",
        fixer_settings=FixerSettings(force_summary_period=False),
    )


def test_noforce_summary_blank_line() -> None:
    """Test that blank line after short description is not enforced when disabled."""
    check_expected_diff(
        "force_summary_blank_line",
        fixer_settings=FixerSettings(
            force_summary_blank_line=False, force_summary_period=False
        ),
        reference_name="force_summary_blank_line.noforce",
    )


def test_example_order() -> None:
    """Test that the "Examples" section comes after all other sections."""
    check_expected_diff("example_order")


def test_except_handling() -> None:
    """Test that caught raises are suppressed and uncaught raises are reported."""
    check_expected_diff("except_handling")


@pytest.mark.skipif(sys.version_info < (3, 11), reason="ExceptionGroup requires 3.11+")
def test_except_star_handling() -> None:
    """Test ExceptionGroup and try/except* raise handling."""
    check_expected_diff("except_star_handling")
