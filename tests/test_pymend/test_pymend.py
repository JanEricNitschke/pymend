"""Test general pymend functionality."""

import pathlib
import shutil
from pathlib import Path

import pymend.pymend as pym
from pymend.docstring_info import FixerSettings

from .util import absdir, get_expected_patch, remove_diff_header


class TestDocStrings:
    """Test correct parsing of docstrings."""

    def setup_class(self) -> None:
        """Set up class by setting file paths."""
        self.myelem = '    def my_method(self, first, second=None, third="value"):'
        self.mydocs = '''        """This is a description of a method.
                It is on several lines.
                Several styles exists:
                    -javadoc,
                    -reST,
                    -cstyle.
                It uses the javadoc style.

                @param first: the 1st argument.
                with multiple lines
                @type first: str
                @param second: the 2nd argument.
                @return: the result value
                @rtype: int
                @raise KeyError: raises exception

                """'''

        self.inifile = absdir("refs/origin_test.py")
        self.jvdfile = absdir("refs/javadoc_test.py")
        self.rstfile = absdir("refs/rest_test.py")
        self.foo = absdir("refs/foo")

        # prepare test file
        txt = ""
        shutil.copyfile(self.inifile, self.jvdfile)
        txt = pathlib.Path(self.jvdfile).read_text()
        txt = txt.replace("@return", ":returns")
        txt = txt.replace("@raise", ":raises")
        txt = txt.replace("@", ":")
        with self.rstfile.open("w", encoding="utf-8") as rstfile:
            rstfile.write(txt)
        with self.foo.open("w", encoding="utf-8") as fooo:
            fooo.write("foo")

    def teardown_class(self) -> None:
        """Tear down class by deleting files."""
        self.jvdfile.unlink()
        self.rstfile.unlink()
        self.foo.unlink()

    def test_parsed_javadoc(self) -> None:
        """Test that javadoc comments get parsed."""
        comment = pym.PyComment(self.inifile, fixer_settings=FixerSettings())
        assert comment.fixed

    def test_windows_rename(self) -> None:
        """Check that renaming works correctly."""
        bar = absdir("bar")
        with bar.open("w", encoding="utf-8") as fbar:
            fbar.write("bar")
        comment = pym.PyComment(self.foo, fixer_settings=FixerSettings())
        comment._windows_rename(Path(bar))
        assert not bar.is_file()
        assert self.foo.is_file()
        foo_txt = pathlib.Path(self.foo).read_text(encoding="utf-8")
        assert foo_txt == "bar"


class TestFilesConversions:
    """Test patch files."""

    def test_case_free_testing(self) -> None:
        """Test correct handling for case where input style in ambiguous."""
        comment = pym.PyComment(
            absdir("refs/free_cases.py"), fixer_settings=FixerSettings()
        )
        result = "".join(comment._docstring_diff())
        assert result == ""

    def test_case_gen_all_params_numpydoc(self) -> None:
        """Test generation of numpydoc patch.

        The file has several functions with no or several parameters,
        so Pymend should produce docstrings in numpydoc format.
        """
        expected = get_expected_patch("params.py.patch.numpydoc.expected")
        comment = pym.PyComment(
            absdir("refs/params.py"), fixer_settings=FixerSettings()
        )
        result = "".join(comment._docstring_diff())
        assert remove_diff_header(result) == remove_diff_header(expected)

    def test_case_no_gen_docs_already_numpydoc(self) -> None:
        """Test that correct format needs no fixing.

        The file has functions with already docstrings in numpydoc format,
        so no docstring should be produced.
        """
        comment = pym.PyComment(
            absdir("refs/docs_already_numpydoc.py"), fixer_settings=FixerSettings()
        )
        result = "".join(comment._docstring_diff())
        assert result == ""
