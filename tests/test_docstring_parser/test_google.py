"""Tests for Google-style docstring routines."""

from typing import Optional

import pytest

from pymend.docstring_parser.common import (
    Docstring,
    DocstringMeta,
    DocstringRaises,
    ParseError,
    RenderingStyle,
)
from pymend.docstring_parser.google import (
    GoogleParser,
    Section,
    SectionType,
    compose,
    parse,
)


def test_google_parser_unknown_section() -> None:
    """Test parsing an unknown section with default GoogleParser."""
    parser = GoogleParser()
    docstring = parser.parse(
        """
        Unknown:
            spam: a
        """
    )
    assert docstring.short_description == "Unknown:"
    assert docstring.long_description == "spam: a"
    assert len(docstring.meta) == 0


def test_google_parser_custom_sections() -> None:
    """Test parsing an unknown section with custom GoogleParser."""
    parser = GoogleParser(
        [
            Section("DESCRIPTION", "desc", SectionType.SINGULAR),
            Section("ARGUMENTS", "param", SectionType.MULTIPLE),
            Section("ATTRIBUTES", "attribute", SectionType.MULTIPLE),
            Section("EXAMPLES", "examples", SectionType.SINGULAR),
        ],
        title_colon=False,
    )
    docstring = parser.parse(
        """
        DESCRIPTION
            This is the description.

        ARGUMENTS
            arg1: first arg
            arg2: second arg

        ATTRIBUTES
            attr1: first attribute
            attr2: second attribute

        EXAMPLES
            Many examples
            More examples
        """
    )

    assert docstring.short_description is None
    assert docstring.long_description is None
    assert len(docstring.meta) == 6
    assert docstring.meta[0].args == ["desc"]
    assert docstring.meta[0].description == "This is the description."
    assert docstring.meta[1].args == ["param", "arg1"]
    assert docstring.meta[1].description == "first arg"
    assert docstring.meta[2].args == ["param", "arg2"]
    assert docstring.meta[2].description == "second arg"
    assert docstring.meta[3].args == ["attribute", "attr1"]
    assert docstring.meta[3].description == "first attribute"
    assert docstring.meta[4].args == ["attribute", "attr2"]
    assert docstring.meta[4].description == "second attribute"
    assert docstring.meta[5].args == ["examples"]
    assert docstring.meta[5].description == "Many examples\nMore examples"


def test_google_parser_custom_sections_single_param() -> None:
    """Test parsing an unknown section with custom GoogleParser."""
    parser = GoogleParser(
        [
            Section("DESCRIPTION", "desc", SectionType.SINGULAR),
            Section("ARGUMENTS", "param", SectionType.SINGULAR),
        ],
        title_colon=False,
    )
    with pytest.raises(ParseError):
        parser.parse(
            """
            DESCRIPTION
                This is the description.

            ARGUMENTS
                arg1: first arg
            """
        )


def test_google_parser_custom_sections_single_raises() -> None:
    """Test parsing an unknown section with custom GoogleParser."""
    parser = GoogleParser(
        [
            Section("DESCRIPTION", "desc", SectionType.SINGULAR),
            Section("RAISES", "raises", SectionType.SINGULAR),
        ],
        title_colon=False,
    )
    docstring = parser.parse(
        """
            DESCRIPTION
                This is the description.

            RAISES
                Something gets raised
            """
    )
    assert len(docstring.meta) == 2
    assert docstring.meta[0].args == ["desc"]
    assert docstring.meta[0].description == "This is the description."
    assert docstring.meta[1].args == ["raises"]
    assert docstring.meta[1].description == "Something gets raised"
    assert docstring.meta[1].type_name is None


def test_google_parser_custom_sections_other_multi() -> None:
    """Test parsing an unknown section with custom GoogleParser."""
    parser = GoogleParser(
        [
            Section("WEIRD", "weird", SectionType.MULTIPLE),
        ],
        title_colon=False,
    )
    docstring = parser.parse(
        """
            WEIRD
                weird1: stuff
                weird2: more stuff
            """
    )
    assert len(docstring.meta) == 2
    assert docstring.meta[0].args == ["weird", "weird1"]
    assert docstring.meta[0].description == "stuff"
    assert docstring.meta[1].args == ["weird", "weird2"]
    assert docstring.meta[1].description == "more stuff"


def test_google_parser_custom_sections_after() -> None:
    """Test parsing an unknown section with custom GoogleParser configuration.

    Configuration set at a runtime.
    """
    parser = GoogleParser(title_colon=False)
    parser.add_section(Section("Note", "note", SectionType.SINGULAR))
    docstring = parser.parse(
        """
        short description

        Note:
            a note
        """
    )
    assert docstring.short_description == "short description"
    assert docstring.long_description == "Note:\n    a note"

    docstring = parser.parse(
        """
        short description

        Note a note
        """
    )
    assert docstring.short_description == "short description"
    assert docstring.long_description == "Note a note"

    docstring = parser.parse(
        """
        short description

        Note
            a note
        """
    )
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["note"]
    assert docstring.meta[0].description == "a note"


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
            Args:
                asd:
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
            Args:
                asd:
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
            Args:
                asd:
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
            Args:
                asd:
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

            Args:
                asd:
            """,
            "Short description",
            "First line\n    Second line",
            True,
            True,
        ),
        (
            """
            Args:
                asd:
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

        Args:
            spam: asd
                1
                    2
                3
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 1
    assert docstring.meta[0].args == ["param", "spam"]
    assert docstring.meta[0].arg_name == "spam"
    assert docstring.meta[0].description == "asd\n1\n    2\n3"


def test_default_args() -> None:
    """Test parsing default arguments."""
    docstring = parse(
        """A sample function

A function the demonstrates docstrings

Args:
    arg1 (int): The firsty arg
    arg2 (str): The second arg
    arg3 (float, optional): The third arg. Defaults to 1.0.
    arg4 (Optional[Dict[str, Any]], optional): The last arg. Defaults to None.
    arg5 (str, optional): The fifth arg. Defaults to DEFAULT_ARG5.

Returns:
    Mapping[str, Any]: The args packed in a mapping
"""
    )
    assert docstring is not None
    assert len(docstring.params) == 5

    arg4 = docstring.params[3]
    assert arg4.arg_name == "arg4"
    assert arg4.is_optional
    assert arg4.type_name == "Optional[Dict[str, Any]]"
    assert arg4.default == "None"
    assert arg4.description == "The last arg. Defaults to None."


def test_multiple_meta() -> None:
    """Test parsing multiple meta."""
    docstring = parse(
        """
        Short description

        Args:
            spam: asd
                1
                    2
                3

        Raises:
            bla: herp
            yay: derp
        """
    )
    assert docstring.short_description == "Short description"
    assert len(docstring.meta) == 3
    assert docstring.meta[0].args == ["param", "spam"]
    assert docstring.meta[0].arg_name == "spam"
    assert docstring.meta[0].description == "asd\n1\n    2\n3"
    assert docstring.meta[1].args == ["raises", "bla"]
    assert docstring.meta[1].type_name == "bla"
    assert docstring.meta[1].description == "herp"
    assert docstring.meta[2].args == ["raises", "yay"]
    assert docstring.meta[2].type_name == "yay"
    assert docstring.meta[2].description == "derp"


def test_params() -> None:
    """Test parsing params."""
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        Args:
            name: description 1
            priority (int): description 2
            sender (str?): description 3
            ratio (Optional[float], optional): description 4
        """
    )
    assert len(docstring.params) == 4
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == "description 1"
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].description == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[3].arg_name == "ratio"
    assert docstring.params[3].type_name == "Optional[float]"
    assert docstring.params[3].description == "description 4"
    assert docstring.params[3].is_optional

    docstring = parse(
        """
        Short description

        Args:
            name: description 1
                with multi-line text
            priority (int): description 2
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == ("description 1\nwith multi-line text")
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"


def test_attributes() -> None:
    """Test parsing attributes."""
    docstring = parse("Short description")
    assert len(docstring.params) == 0

    docstring = parse(
        """
        Short description

        Attributes:
            name: description 1
            priority (int): description 2
            sender (str?): description 3
            ratio (Optional[float], optional): description 4
        """
    )
    assert len(docstring.params) == 4
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == "description 1"
    assert not docstring.params[0].is_optional
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"
    assert not docstring.params[1].is_optional
    assert docstring.params[2].arg_name == "sender"
    assert docstring.params[2].type_name == "str"
    assert docstring.params[2].description == "description 3"
    assert docstring.params[2].is_optional
    assert docstring.params[3].arg_name == "ratio"
    assert docstring.params[3].type_name == "Optional[float]"
    assert docstring.params[3].description == "description 4"
    assert docstring.params[3].is_optional

    docstring = parse(
        """
        Short description

        Attributes:
            name: description 1
                with multi-line text
            priority (int): description 2
        """
    )
    assert len(docstring.params) == 2
    assert docstring.params[0].arg_name == "name"
    assert docstring.params[0].type_name is None
    assert docstring.params[0].description == ("description 1\nwith multi-line text")
    assert docstring.params[1].arg_name == "priority"
    assert docstring.params[1].type_name == "int"
    assert docstring.params[1].description == "description 2"


def test_returns_1() -> None:
    """Test parsing returns."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.returns is None
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 0

    docstring = parse(
        """
        Short description
        Returns:
            description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name is None
    assert docstring.returns.description == "description"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Short description
        Returns:
            description with: a colon!
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name is None
    assert docstring.returns.description == "description with: a colon!"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Short description
        Returns:
            int: description
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == "description"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Short description
        Returns:
            str | int|None  | bool: A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "str | int|None  | bool"
    assert docstring.returns.description == "A description: with a colon"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Returns:
            Optional[Mapping[str, List[int]]]: A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "Optional[Mapping[str, List[int]]]"
    assert docstring.returns.description == "A description: with a colon"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns


def test_returns_2() -> None:
    """Test parsing returns."""
    docstring = parse(
        """
        Returns:
            list[int] | None: A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "list[int] | None"
    assert docstring.returns.description == "A description: with a colon"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Returns:
            tuple[int, int] | None: A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "tuple[int, int] | None"
    assert docstring.returns.description == "A description: with a colon"
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """
        Args:
            area_points (dict[str, list[tuple[float, float]]]): Dict mapping each place
                to the x and y coordinates of each area inside it.
            z_s  (dict[str, list]): Dict mapping each place to the z coordinates of each
                area inside it.

        Returns:
            area_points (dict[str, list[tuple[float, float]]]): Dict mapping each place
                to the x and y coordinates of each area inside it.
            z_s  (dict[str, list]): Dict mapping each place to the z coordinates of each
                area inside it.
        """
    )
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 2
    assert docstring.params[0].type_name == "dict[str, list[tuple[float, float]]]"
    assert docstring.params[1].type_name == "dict[str, list]"
    assert docstring.many_returns[0].type_name == "dict[str, list[tuple[float, float]]]"
    assert docstring.many_returns[1].type_name == "dict[str, list]"

    docstring = parse(
        """
        Short description
        Yields:
            int: description
        """
    )
    assert docstring.returns is None

    docstring = parse(
        """
        Short description
        Returns:
            int: description
            with much text

            even some spacing
        """
    )
    assert docstring.returns is not None
    assert docstring.returns.type_name == "int"
    assert docstring.returns.description == (
        "description\nwith much text\n\neven some spacing"
    )
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 1
    assert docstring.many_returns[0] == docstring.returns

    docstring = parse(
        """Returns the graph distance between two areas.

        Returns:
            length (float): Distance between two areas as length of the path
            discovered_path (list[TileId]): Path between the two areas as list of nodes
        """
    )
    assert docstring.many_returns is not None
    assert len(docstring.many_returns) == 2
    assert docstring.many_returns[0].type_name == "float"
    assert docstring.many_returns[1].type_name == "list[TileId]"


def test_yields() -> None:
    """Test parsing returns."""
    docstring = parse(
        """
        Short description
        """
    )
    assert docstring.yields is None

    docstring = parse(
        """
        Returns:
            int: description
        """
    )
    assert docstring.yields is None

    docstring = parse(
        """
        Short description
        Yields:
            description
        """
    )
    assert docstring.yields is not None
    assert docstring.yields.type_name is None
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator is True

    docstring = parse(
        """
        Short description
        Yields:
            description with: a colon!
        """
    )
    assert docstring.yields is not None
    assert docstring.yields.type_name is None
    assert docstring.yields.description == "description with: a colon!"
    assert docstring.yields.is_generator is True

    docstring = parse(
        """
        Short description
        Yields:
            int: description
        """
    )
    assert docstring.yields is not None
    assert docstring.yields.type_name == "int"
    assert docstring.yields.description == "description"
    assert docstring.yields.is_generator is True

    docstring = parse(
        """
        Yields:
            Optional[Mapping[str, List[int]]]: A description: with a colon
        """
    )
    assert docstring.yields is not None
    assert docstring.yields.type_name == "Optional[Mapping[str, List[int]]]"
    assert docstring.yields.description == "A description: with a colon"
    assert docstring.yields.is_generator is True

    docstring = parse(
        """
        Short description
        Yields:
            int: description
            with much text

            even some spacing
        """
    )
    assert docstring.yields is not None
    assert docstring.yields.type_name == "int"
    assert docstring.yields.description == (
        "description\nwith much text\n\neven some spacing"
    )
    assert docstring.yields.is_generator is True

    docstring = parse(
        """
        Returns:
            int: description with return first

        Yields:
            Optional[Mapping[str, List[int]]]: A description: with a colon
        """
    )
    assert docstring.returns is not None
    assert docstring.yields is not None
    assert docstring.yields.type_name != docstring.returns.type_name

    docstring = parse(
        """
        Yields:
            Optional[Mapping[str, List[int]]]: A description: with a colon
        Returns:
            int: description with return last
        """
    )
    assert docstring.returns is not None
    assert docstring.yields is not None
    assert docstring.yields.type_name == "Optional[Mapping[str, List[int]]]"
    assert docstring.returns.type_name == "int"


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
        Raises:
            ValueError: description
        """
    )
    assert len(docstring.raises) == 1
    assert docstring.raises[0].type_name == "ValueError"
    assert docstring.raises[0].description == "description"


def test_examples() -> None:
    """Test parsing examples."""
    docstring = parse(
        """
        Short description
        Example:
            example: 1
        """
    )
    assert len(docstring.examples) == 1
    assert docstring.examples[0].description == "example: 1"


def test_broken_meta() -> None:
    """Test parsing broken meta."""
    with pytest.raises(ParseError):
        parse("Args:")

    with pytest.raises(ParseError):
        parse("Args:\n    herp derp")


def test_unknown_meta() -> None:
    """Test parsing unknown meta."""
    docstring = parse(
        """Short desc

        Unknown 0:
            title0: content0

        Args:
            arg0: desc0
            arg1: desc1

        Unknown1:
            title1: content1

        Unknown2:
            title2: content2
        """
    )

    assert docstring.params[0].arg_name == "arg0"
    assert docstring.params[0].description == "desc0"
    assert docstring.params[1].arg_name == "arg1"
    assert docstring.params[1].description == "desc1"


def test_broken_arguments() -> None:
    """Test parsing broken arguments."""
    with pytest.raises(ParseError):
        parse(
            """This is a test

            Args:
                param - poorly formatted
            """
        )


def test_empty_example() -> None:
    """Test parsing empty examples section."""
    docstring = parse(
        """Short description

        Example:

        Raises:
            IOError: some error
        """
    )

    assert len(docstring.examples) == 1
    assert docstring.examples[0].args == ["examples"]
    assert docstring.examples[0].description == ""


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
            Meta:
                asd
            """,
            "Short description\nMeta:\n    asd",
        ),
        (
            """
            Short description
            Long description
            Meta:
                asd
            """,
            "Short description\nLong description\nMeta:\n    asd",
        ),
        (
            """
            Short description
            First line
                Second line
            Meta:
                asd
            """,
            "Short description\nFirst line\n    Second line\nMeta:\n    asd",
        ),
        (
            """
            Short description

            First line
                Second line
            Meta:
                asd
            """,
            "Short description\n\nFirst line\n    Second line\nMeta:\n    asd",
        ),
        (
            """
            Short description

            First line
                Second line

            Meta:
                asd
            """,
            "Short description\n\nFirst line\n    Second line\n\nMeta:\n    asd",
        ),
        (
            """
            Short description

            Meta:
                asd
                    1
                        2
                    3
            """,
            "Short description\n\nMeta:\n    asd\n        1\n            2\n        3",
        ),
        (
            """
            Short description

            Meta1:
                asd
                1
                    2
                3
            Meta2:
                herp
            Meta3:
                derp
            """,
            "Short description\n"
            "\n"
            "Meta1:\n"
            "    asd\n"
            "    1\n"
            "        2\n"
            "    3\n"
            "Meta2:\n"
            "    herp\n"
            "Meta3:\n"
            "    derp",
        ),
        (
            """
            Short description

            Args:
                name: description 1
                priority (int): description 2
                sender (str, optional): description 3
                message (str, optional): description 4, defaults to 'hello'
                multiline (str?):
                    long description 5,
                        defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "Args:\n"
            "    name: description 1\n"
            "    priority (int): description 2\n"
            "    sender (str?): description 3\n"
            "    message (str?): description 4, defaults to 'hello'\n"
            "    multiline (str?): long description 5,\n"
            "        defaults to 'bye'",
        ),
        (
            """
            Short description
            Raises:
                ValueError: description
            """,
            "Short description\nRaises:\n    ValueError: description",
        ),
        (
            """
            Short description

            Returns:
                int: description
            """,
            "Short description\n\nReturns:\n    int: description",
        ),
        (
            """
            Short description

            Yields:
                int: description
            """,
            "Short description\n\nYields:\n    int: description",
        ),
        (
            """
            Short description

            Yields:
                Optional[Mapping[str, List[int]]]: A description: with a colon

            Returns:
                int: description with return last
            """,
            "Short description\n"
            "\n"
            "Returns:\n"
            "    int: description with return last\n"
            "\n"
            "Yields:\n"
            "    Optional[Mapping[str, List[int]]]: A description: with a colon",
        ),
    ],
)
def test_compose(source: str, expected: str) -> None:
    """Test compose in default mode."""
    assert compose(parse(source)) == expected


def test_compose_docstring() -> None:
    """Test compose from pre-built docstring."""
    source = Docstring()
    source.meta = [
        DocstringRaises([], None, None),
        DocstringMeta(["meta"], "Some description"),
        DocstringMeta(["meta"], ""),
    ]
    expected = """\
Raises:


Meta:
    Some description

Meta:"""
    assert compose(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            """
            Short description

            Args:
                name: description 1
                priority (int): description 2
                sender (str, optional): description 3
                message (str, optional): description 4, defaults to 'hello'
                multiline (str?):
                    long description 5,
                        defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "Args:\n"
            "    name: description 1\n"
            "    priority (int): description 2\n"
            "    sender (str, optional): description 3\n"
            "    message (str, optional): description 4, defaults to 'hello'\n"
            "    multiline (str, optional): long description 5,\n"
            "        defaults to 'bye'",
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

            Args:
                name: description 1
                priority (int): description 2
                sender (str, optional): description 3
                message (str, optional): description 4, defaults to 'hello'
                multiline (str?):
                    long description 5,
                        defaults to 'bye'
            """,
            "Short description\n"
            "\n"
            "Args:\n"
            "    name:\n"
            "        description 1\n"
            "    priority (int):\n"
            "        description 2\n"
            "    sender (str, optional):\n"
            "        description 3\n"
            "    message (str, optional):\n"
            "        description 4, defaults to 'hello'\n"
            "    multiline (str, optional):\n"
            "        long description 5,\n"
            "        defaults to 'bye'",
        ),
    ],
)
def test_compose_expanded(source: str, expected: str) -> None:
    """Test compose in expanded mode."""
    assert compose(parse(source), rendering_style=RenderingStyle.EXPANDED) == expected
