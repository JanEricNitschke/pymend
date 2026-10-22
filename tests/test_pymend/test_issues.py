"""Testing issues raised on github."""

import itertools
from pathlib import Path

import pytest

import pymend.docstring_parser as dsp
import pymend.pymend as pym
from pymend.const import DocstringForceMode
from pymend.docstring_info import FixerSettings

from .test_numpyoutput import check_expected_diff
from .util import absdir


class TestIssues:
    """Class for testing raised issues."""

    def test_issue_30(self) -> None:
        """Test issue 30.

        https://github.com/dadadel/pyment/issues/30
        """
        # if file starting with a function/class definition, patching the file
        # will remove the first line!
        comment = pym.PyComment(
            absdir("refs/issue30.py"), fixer_settings=FixerSettings()
        )
        try:
            comment._docstring_diff()
        except Exception as e:  # noqa: BLE001
            pytest.fail(f'Raised exception: "{e}"')

    def test_issue_49(self) -> None:
        """Test issue 49.

        https://github.com/dadadel/pyment/issues/49
        """
        # Title: If already numpydoc format, will remove the Raises section
        # If the last section in a numpydoc docstring is a `Raises` section,
        # it will be removed if the output format is also set to numpydoc
        comment = pym.PyComment(
            absdir("refs/issue49.py"), fixer_settings=FixerSettings()
        )
        result = "".join(comment._docstring_diff())
        assert result == ""

    def test_issue_207_google(self) -> None:
        """Multi-return entries are collapsed for Google output.

        https://github.com/JanEricNitschke/pymend/issues/207
        """
        check_expected_diff("issue207", output_style=dsp.DocstringStyle.GOOGLE)

    def test_issue_207_rest(self) -> None:
        """Multi-return entries are collapsed for reST output.

        https://github.com/JanEricNitschke/pymend/issues/207
        """
        check_expected_diff("issue207", output_style=dsp.DocstringStyle.REST)

    def test_issue_207_epydoc(self) -> None:
        """Multi-return entries are collapsed for Epydoc output.

        https://github.com/JanEricNitschke/pymend/issues/207
        """
        check_expected_diff("issue207", output_style=dsp.DocstringStyle.EPYDOC)

    def test_issue_369_property_needs_no_returns(self, tmp_path: Path) -> None:
        """A documented property needs no Returns section.

        https://github.com/JanEricNitschke/pymend/issues/369
        """
        source = tmp_path / "test_pymend_property.py"
        source.write_text(
            '''class TestClass:
    def __init__(self, a: int):
        self._a = a

    @property
    def a(self) -> int:
        """The value of a."""
        return self._a
''',
            encoding="utf-8",
        )
        comment = pym.PyComment(
            source,
            fixer_settings=FixerSettings(force_docstrings=DocstringForceMode.OFF),
        )
        assert "".join(comment._docstring_diff()) == ""
        assert comment.report_issues() == (0, "")

    @pytest.mark.parametrize(
        "source_text",
        [
            '''def value() -> int:
    """The value."""
    return 1
''',
            '''class TestClass:
    def value(self) -> int:
        """The value."""
        return 1
''',
        ],
        ids=["function", "method"],
    )
    def test_issue_369_ordinary_returns_still_required(
        self, tmp_path: Path, source_text: str
    ) -> None:
        """Ordinary functions and methods still require a Returns section."""
        source = tmp_path / "ordinary.py"
        source.write_text(source_text, encoding="utf-8")
        comment = pym.PyComment(
            source,
            fixer_settings=FixerSettings(force_docstrings=DocstringForceMode.OFF),
        )
        assert "Missing return value." in comment.report_issues()[1]
        assert "Returns" in "".join(comment._docstring_diff())

    def test_issue_369_custom_property_decorator(self, tmp_path: Path) -> None:
        """Configured property decorators have the same return behavior."""
        source = tmp_path / "custom_property.py"
        source.write_text(
            '''class TestClass:
    @cached_property
    def value(self) -> int:
        """The value."""
        return 1
''',
            encoding="utf-8",
        )
        comment = pym.PyComment(
            source,
            fixer_settings=FixerSettings(
                force_docstrings=DocstringForceMode.OFF,
                property_decorators=["cached_property"],
            ),
        )
        assert "".join(comment._docstring_diff()) == ""
        assert comment.report_issues() == (0, "")

    def test_issue_369_existing_returns_kept(self, tmp_path: Path) -> None:
        """An explicit property Returns section remains supported."""
        source = tmp_path / "documented_property.py"
        source.write_text(
            '''class TestClass:
    @property
    def value(self) -> int:
        """The value.

        Returns
        -------
        int
            The current value.
        """
        return 1
''',
            encoding="utf-8",
        )
        comment = pym.PyComment(
            source,
            fixer_settings=FixerSettings(force_docstrings=DocstringForceMode.OFF),
        )
        assert "".join(comment._docstring_diff()) == ""
        assert comment.report_issues() == (0, "")

    @pytest.mark.skip(reason="Currently an unsolved problem.")
    @pytest.mark.parametrize(
        ("input_style", "output_style"),
        [
            (input_style, output_style)
            for input_style, output_style in itertools.product(
                dsp.DocstringStyle,
                dsp.DocstringStyle,
            )
        ],
    )
    def test_stability_with_explicit_input_style(
        self, input_style: dsp.DocstringStyle, output_style: dsp.DocstringStyle
    ) -> None:
        """Stability check must use output_style as input for the second pass.

        When an explicit input_style is provided, the first pass converts
        from input_style to output_style. The stability check re-runs on
        the output, which is now in output_style format. The second pass
        must parse using output_style (not the original input_style),
        otherwise parsing the wrong format causes an AssertionError.
        """
        comment = pym.PyComment(
            absdir("refs/stability_input_style.py"),
            input_style=input_style,
            output_style=output_style,
            fixer_settings=FixerSettings(),
        )
        assert comment.fixed
