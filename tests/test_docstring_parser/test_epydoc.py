"""Tests for epydoc-style docstring routines."""

from typing import Optional

import pytest

from pymend.docstring_parser.common import (
    Docstring,
    DocstringRaises,
    DocstringReturns,
    ParseError,
    RenderingStyle,
)
from pymend.docstring_parser.epydoc import (
    StreamToken,
    _add_meta_information,
    compose,
    parse,
)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None:
    """Test parsing short description."""
    docstring = parse(source)
    assert docstring.short_description == expected
    assert docstring.long_description is None
    assert not docstring.meta


@pytest.mark.parametrize(
    ("source", "expected_short_desc", "expected_long_desc", "expected_blank"),
    [
        (
            "Short description\n\nLong description",
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            """,
            "Short description",
            "Long description",
            True,
        ),
        (
            """
            Short description

            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            True,
        ),
        (
            "Short description\nLong description",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            """,
            "Short description",
            "Long description",
            False,
        ),
        (
            "\nShort description\nLong description\n",
            "Short description",
            "Long description",
            False,
        ),
        (
            """
            Short description
            Long description
            Second line
            """,
            "Short description",
            "Long description\nSecond line",
            False,
        ),
    ],
)
def test_long_description(
    source: str,
    expected_short_desc: str,
    expected_long_desc: str,
    *,
    expected_blank: bool,
) -> None:
    """Test parsing long description."""
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank
    assert not docstring.meta


@pytest.mark.parametrize(
    (
        "source",
        "expected_short_desc",
        "expected_long_desc",
        "expected_blank_short_desc",
        "expected_blank_long_desc",
    ),
    [
        (
            """
            Short description
            @meta: asd
            """,
            "Short description",
            None,
            False,
            False,
        ),
        (
            """
            Short description
            Long description
            @meta: asd
            """,
            "Short description",
            "Long description",
            False,
            False,
        ),
        (
            """
            Short description
            First line
                Second line
            @meta: asd
            """,
            "Short description",
            "First line\n    Second line",
            False,
            False,
        ),
        (
            """
            Short description

            First line
                Second line
            @meta: asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            False,
        ),
        (
            """
            Short description

            First line
                Second line

            @meta: asd
            """,
            "Short description",
            "First line\n    Second line",
            True,
            True,
        ),
        (
            """
            @meta: asd
            """,
            None,
            None,
            False,
            False,
        ),
    ],
)
def test_meta_newlines(
    source: str,
    expected_short_desc: Optional[str],
    expected_long_desc: Optional[str],
    *,
    expected_blank_short_desc: bool,
    expected_blank_long_desc: bool,
) -> None:
    """Test parsing newlines around description sections."""
    docstring = parse(source)
    assert docstring.short_description == expected_short_desc
    assert docstring.long_description == expected_long_desc
    assert docstring.blank_after_short_description == expected_blank_short_desc
    assert docstring.blank_after_long_description == expected_blank_long_desc
    assert len(docstring.meta) == 1


def test_meta_with_multiline_description() -> None:
    """Test parsing multiline meta documentation."""
    docstring = parse(
        """
        Short description

        @meta: asd
            1
                2
            3
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["meta"]
    assert docstring.meta[0].description == "asd\n1\n    2\n3"


def test_multiple_meta() -> None:
    """Test parsing multiple meta."""
    docstring = parse(
        """
        Short description

        @meta1: asd
            1
                2
            3
        @meta2: herp
        @meta3: derp
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 3
    assert docstring.meta[0].args == ["meta1"]
    assert docstring.meta[0].description == "asd\n1\n    2\n3"
    assert docstring.meta[1].args == ["meta2"]
    assert docstring.meta[1].description == "herp"
    assert docstring.meta[2].args == ["meta3"]
    assert docstring.meta[2].description == "derp"


def test_meta_with_args() -> None:
    """Test parsing meta with additional arguments."""
    docstring = parse(
        """
        Short description

        @meta ene due rabe: asd
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["meta", "ene", "due", "rabe"]
    assert docstring.meta[0].description == "asd"


def test_unknown_meta() -> None:
    """Test for correct behaviour when unknown section is encountered."""
    with pytest.raises(ParseError):
        _add_meta_information([StreamToken("weird", "", [], "")], {}, None)


def test_params() -> None:
    """Test parsing params."""
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        @param name: description 1
        @param priority: description 2
        @type priority: int
        @param sender: description 3
        @type sender: str?
        @param message: description 4, defaults to 'hello'
        @type message: str?
        @param multiline: long description 5,
        defaults to 'bye'
        @type multiline: str?
        """
    )
    assert len(docstring.params) == 5
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == "description 1"
    assert docstring.params[0].default is None
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[1].default is None
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].description == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[2].default is None
    assert docstring.params[3].arg_name == "message"
    assert docstring.params[3].type_name == "str"
    assert docstring.params[3].description == "description 4, defaults to 'hello'"
    assert docstring.params[3].is_optional
    assert docstring.params[3].default == "'hello'"
    assert docstring.params[4].arg_name == "multiline"
    assert docstring.params[4].type_name == "str"
    assert docstring.params[4].description == "long description 5,\ndefaults to 'bye'"
    assert docstring.params[4].is_optional
    assert docstring.params[4].default == "'bye'"


def test_returns() -> None:
    """Test parsing returns."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None

    docstring = parse(
        """
        Short description
        @return: description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name is None
    assert docstring.returns.description == "description"
    assert not docstring.returns.is_generator

    docstring = parse(
        """
        Short description
        @return: description
        @rtype: int
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == "description"
    assert not docstring.returns.is_generator


def test_yields() -> None:
    """Test parsing yields."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None

    docstring = parse(
        """
        Short description
        @yield: description
        """
    )
    assert docstring.returns is None
    assert docstring.yields is not None
    assert docstring.yields.type_name is None
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator

    docstring = parse(
        """
        Short description
        @yield: description
        @ytype: int
        """
    )
    assert docstring.returns is None
    assert docstring.yields is not None
    assert docstring.yields.type_name == "int"
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator

    docstring = parse(
        """
        Short description
        @return: description
        @rtype: str
        @yield: description
        @ytype: int
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "str"
    assert docstring.returns.description == "description"
    assert not docstring.returns.is_generator
    assert docstring.yields is not None
    assert docstring.yields.type_name == "int"
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator


def test_raises() -> None:
    """Test parsing raises."""
    docstring = parse(
        """
        Short description
        """
    )
    assert len(docstring.raises) == 0

    docstring = parse(
        """
        Short description
        @raise: description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name is None
    assert docstring.raises[0].description == "description"

    docstring = parse(
        """
        Short description
        @raise ValueError: description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name == "ValueError"
    assert docstring.raises[0].description == "description"


def test_broken_meta() -> None:
    """Test parsing broken meta."""
    with pytest.raises(ParseError):
        parse("@")

    with pytest.raises(ParseError):
        parse("@param herp derp")

    with pytest.raises(ParseError):
        parse("@param: invalid")

    with pytest.raises(ParseError):
        parse("@param with too many args: desc")

    # these should not raise any errors
    parse("@sthstrange: desc")


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("", ""),
        ("\n", ""),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
        (
            "Short description\n\nLong description",
            "Short description\n\nLong description",
        ),
        (
            """
            Short description

            Long description
            """,
            "Short description\n\nLong description",
        ),
        (
            """
            Short description

            Long description
            Second line
            """,
            "Short description\n\nLong description\nSecond line",
        ),
        (
            "Short description\nLong description",
            "Short description\nLong description",
        ),
        (
            """
            Short description
            Long description
            """,
            "Short description\nLong description",
        ),
        (
            "\nShort description\nLong description\n",
            "Short description\nLong description",
        ),
        (
            """
            Short description
            Long description
            Second line
            """,
            "Short description\nLong description\nSecond line",
        ),
        (
            """
            Short description
            @meta: asd
            """,
            "Short description\n@meta: asd",
        ),
        (
            """
            Short description
            Long description
            @meta: asd
            """,
            "Short description\nLong description\n@meta: asd",
        ),
        (
            """
            Short description
            First line
                Second line
            @meta: asd
            """,
            "Short description\nFirst line\n    Second line\n@meta: asd",
        ),
        (
            """
            Short description

            First line
                Second line
            @meta: asd
            """,
            "Short description\n\nFirst line\n    Second line\n@meta: asd",
        ),
        (
            """
            Short description

            First line
                Second line

            @meta: asd
            """,
            "Short description\n\nFirst line\n    Second line\n\n@meta: asd",
        ),
        (
            """
            @meta: asd
            """,
            "@meta: asd",
        ),
        (
            """
            Short description

            @meta: asd
                1
                    2
                3
            """,
            "Short description\n\n@meta: asd\n    1\n        2\n    3",
        ),
        (
            """
            Short description

            @meta1: asd
                1
                    2
                3
            @meta2: herp
            @meta3: derp
            """,
            "Short description\n"
            "\n@meta1: asd\n"
            "    1\n"
            "        2\n"
            "    3\n@meta2: herp\n"
            "@meta3: derp",
        ),
        (
            """
            Short description

            @meta ene due rabe: asd
            """,
            "Short description\n\n@meta ene due rabe: asd",
        ),
        (
            """
            Short description

            @param name: description 1
            @param priority: description 2
            @type priority: int
            @param sender: description 3
            @type sender: str?
            @type message: str?
            @param message: description 4, defaults to 'hello'
            @type multiline: str?
            @param multiline: long description 5,
                defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "@param name: description 1\n"
            "@type priority: int\n"
            "@param priority: description 2\n"
            "@type sender: str?\n"
            "@param sender: description 3\n"
            "@type message: str?\n"
            "@param message: description 4, defaults to 'hello'\n"
            "@type multiline: str?\n"
            "@param multiline: long description 5,\n"
            "    defaults to 'bye'",
        ),
        (
            """
            Short description
            @raise: description
            """,
            "Short description\n@raise: description",
        ),
        (
            """
            Short description
            @raise ValueError: description
            """,
            "Short description\n@raise ValueError: description",
        ),
        (
            """
            Short description
            @return: description
            @rtype: int
            """,
            "Short description\n@rtype: int\n@return: description",
        ),
        (
            """
            Short description
            @yield: description
            @ytype: int
            """,
            "Short description\n@ytype: int\n@yield: description",
        ),
    ],
)
def test_compose(source: str, expected: str) -> None:
    """Test compose in default mode."""
    assert compose(parse(source)) == expected


def test_compose_docstring() -> None:
    """Test compose in default mode."""
    source = Docstring()
    source.meta = [
        DocstringRaises([], None, None),
        DocstringReturns([], None, None, is_generator=False),
    ]
    expected = "@raise:"
    assert compose(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
            Short description

            @param name: description 1
            @param priority: description 2
            @type priority: int
            @param sender: description 3
            @type sender: str?
            @type message: str?
            @param message: description 4, defaults to 'hello'
            @type multiline: str?
            @param multiline: long description 5,
                defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "@param name:\n"
            "    description 1\n"
            "@type priority: int\n"
            "@param priority:\n"
            "    description 2\n"
            "@type sender: str?\n"
            "@param sender:\n"
            "    description 3\n"
            "@type message: str?\n"
            "@param message:\n"
            "    description 4, defaults to 'hello'\n"
            "@type multiline: str?\n"
            "@param multiline:\n"
            "    long description 5,\n"
            "    defaults to 'bye'",
        ),
    ],
)
def test_compose_clean(source: str, expected: str) -> None:
    """Test compose in clean mode."""
    assert compose(parse(source), rendering_style=RenderingStyle.CLEAN) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
            Short description

            @param name: description 1
            @param priority: description 2
            @type priority: int
            @param sender: description 3
            @type sender: str?
            @type message: str?
            @param message: description 4, defaults to 'hello'
            @type multiline: str?
            @param multiline: long description 5,
                defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "@param name:\n"
            "    description 1\n"
            "@type priority:\n"
            "    int\n"
            "@param priority:\n"
            "    description 2\n"
            "@type sender:\n"
            "    str?\n"
            "@param sender:\n"
            "    description 3\n"
            "@type message:\n"
            "    str?\n"
            "@param message:\n"
            "    description 4, defaults to 'hello'\n"
            "@type multiline:\n"
            "    str?\n"
            "@param multiline:\n"
            "    long description 5,\n"
            "    defaults to 'bye'",
        ),
    ],
)
def test_compose_expanded(source: str, expected: str) -> None:
    """Test compose in expanded mode."""
    assert compose(parse(source), rendering_style=RenderingStyle.EXPANDED) == expected


def test_short_rtype() -> None:
    """Test abbreviated docstring with only return type information."""
    string = "Short description.\n\n@rtype: float"
    docstring = parse(string)
    assert compose(docstring) == string
