"""Testing issues raised on github."""

import itertools

import pytest

import pymend.docstring_parser as dsp
import pymend.pymend as pym
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
