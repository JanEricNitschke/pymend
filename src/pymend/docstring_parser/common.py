"""Common methods for parsing."""

import enum
from collections import UserDict
from dataclasses import dataclass
from typing import TypeAlias, TypeVar

PARAM_KEYWORDS = {
    "param",
    "parameter",
    "arg",
    "argument",
    "attribute",
    "generics",
    "key",
    "keyword",
}
# These could be made into frozen sets
# Then one could create a dictionary
# {KEYWORD: FUNCTION_THAT_HANDLES_THAT_KEYWORD_SECTION}  # noqa: ERA001
RAISES_KEYWORDS = {"raises", "raise", "except", "exception"}
DEPRECATION_KEYWORDS = {"deprecation", "deprecated"}
RETURNS_KEYWORDS = {"return", "returns"}
YIELDS_KEYWORDS = {"yield", "yields"}
EXAMPLES_KEYWORDS = {"example", "examples"}


def clean_str(string: str) -> str | None:
    """Strip a string and return None if it is now empty.

    Parameters
    ----------
    string : str
        String to clean

    Returns
    -------
    str | None
        None of the stripped string is empty. Otherwise the stripped string.
    """
    string = string.strip()
    return string if string != "" else None


class ParseError(RuntimeError):
    """Base class for all parsing related errors."""


class DocstringStyle(enum.Enum):
    """Docstring style."""

    REST = 1
    GOOGLE = 2
    NUMPYDOC = 3
    EPYDOC = 4
    AUTO = 255


class RenderingStyle(enum.Enum):
    """Rendering style when unparsing parsed docstrings."""

    COMPACT = 1
    CLEAN = 2
    EXPANDED = 3


@dataclass
class DocstringMeta:
    """Docstring meta information.

    Symbolizes lines in form of

    Parameters
    ----------
    args : List[str]
        list of arguments. The exact content of this variable is
        dependent on the kind of docstring; it's used to distinguish
        between custom docstring meta information items.
    description : Optional[str]
        associated docstring description.
    """

    args: list[str]
    description: str | None


@dataclass
class DocstringParam(DocstringMeta):
    """DocstringMeta symbolizing :param metadata."""

    arg_name: str
    type_name: str | None
    is_optional: bool | None
    default: str | None


@dataclass
class DocstringReturns(DocstringMeta):
    """DocstringMeta symbolizing :returns metadata."""

    type_name: str | None
    is_generator: bool
    return_name: str | None = None


@dataclass
class DocstringYields(DocstringMeta):
    """DocstringMeta symbolizing :yields metadata."""

    type_name: str | None
    is_generator: bool
    yield_name: str | None = None


@dataclass
class DocstringRaises(DocstringMeta):
    """DocstringMeta symbolizing :raises metadata."""

    type_name: str | None


MainSections: TypeAlias = (
    DocstringParam | DocstringRaises | DocstringReturns | DocstringYields
)


@dataclass
class DocstringDeprecated(DocstringMeta):
    """DocstringMeta symbolizing deprecation metadata."""

    version: str | None


@dataclass
class DocstringExample(DocstringMeta):
    """DocstringMeta symbolizing example metadata."""

    snippet: str | None


K = TypeVar("K")
V = TypeVar("V")


class KeyReturnDict(UserDict[K, V]):
    """Custom dict that returns the key back in missing case."""

    def __missing__(self, key: K) -> K:
        """Return the key.

        Parameters
        ----------
        key : K
            key to look for.

        Returns
        -------
        K
            Returns the key directly.
        """
        return key


class Docstring:
    """Docstring object representation."""

    def __init__(
        self,
        style: DocstringStyle | None = None,
        section_titles: KeyReturnDict[str, str] | None = None,
    ) -> None:
        """Initialize self.

        Parameters
        ----------
        style : DocstringStyle | None
            Style that this docstring was formatted in. (Default value = None)
        """
        self.short_description: str | None = None
        self.long_description: str | None = None
        self.blank_after_short_description: bool = False
        self.blank_after_long_description: bool = False
        self.meta: list[DocstringMeta] = []
        self.style: DocstringStyle | None = style
        self.section_titles: KeyReturnDict[str, str] = section_titles or KeyReturnDict()

    def __bool__(self) -> bool:
        """Return True if the docstring has any content.

        Returns
        -------
        bool
            True if the docstring has any content.
        """
        return any(
            (
                self.short_description,
                self.long_description,
                self.meta,
            )
        )

    @property
    def params(self) -> list[DocstringParam]:
        """Return a list of information on function params.

        Returns
        -------
        list[DocstringParam]
            list of information on function params
        """
        return [item for item in self.meta if isinstance(item, DocstringParam)]

    @property
    def raises(self) -> list[DocstringRaises]:
        """Return a list of the exceptions that the function may raise.

        Returns
        -------
        list[DocstringRaises]
            list of the exceptions that the function may raise.
        """
        return [item for item in self.meta if isinstance(item, DocstringRaises)]

    @property
    def returns(self) -> DocstringReturns | None:
        """Return a single information on function return.

        Takes the first return information.

        Returns
        -------
        DocstringReturns | None
            Single information on function return.
        """
        return next(
            (item for item in self.meta if isinstance(item, DocstringReturns)),
            None,
        )

    @property
    def many_returns(self) -> list[DocstringReturns]:
        """Return a list of information on function return.

        Returns
        -------
        list[DocstringReturns]
            list of information on function return.
        """
        return [item for item in self.meta if isinstance(item, DocstringReturns)]

    @property
    def yields(self) -> DocstringYields | None:
        """Return information on function yield.

        Takes the first generator information.

        Returns
        -------
        DocstringYields | None
            Single information on function yield.
        """
        return next(
            (
                item
                for item in self.meta
                if isinstance(item, DocstringYields) and item.is_generator
            ),
            None,
        )

    @property
    def many_yields(self) -> list[DocstringYields]:
        """Return a list of information on function yields.

        Returns
        -------
        list[DocstringYields]
            list of information on function yields.
        """
        return [item for item in self.meta if isinstance(item, DocstringYields)]

    @property
    def deprecation(self) -> DocstringDeprecated | None:
        """Return a single information on function deprecation notes.

        Returns
        -------
        DocstringDeprecated | None
            single information on function deprecation notes.
        """
        return next(
            (item for item in self.meta if isinstance(item, DocstringDeprecated)),
            None,
        )

    @property
    def examples(self) -> list[DocstringExample]:
        """Return a list of information on function examples.

        Returns
        -------
        list[DocstringExample]
            list of information on function examples.
        """
        return [item for item in self.meta if isinstance(item, DocstringExample)]


def split_description(docstring: Docstring, desc_chunk: str) -> None:
    """Break description into short and long parts.

    Parameters
    ----------
    docstring : Docstring
        Docstring to fill with description information.
    desc_chunk : str
        Chunk of the raw docstring representing the description.
    """
    parts = desc_chunk.split("\n", 1)
    docstring.short_description = parts[0] or None
    if len(parts) > 1:
        long_desc_chunk = parts[1] or ""
        docstring.blank_after_short_description = long_desc_chunk.startswith("\n")
        docstring.blank_after_long_description = long_desc_chunk.endswith("\n\n")
        docstring.long_description = long_desc_chunk.strip() or None


def append_description(docstring: Docstring, parts: list[str]) -> None:
    """Append the docstrings description to the output stream.

    Parameters
    ----------
    docstring : Docstring
        Docstring whose information should be added.
    parts : list[str]
        List of strings representing the output of compose().
        Descriptions should be added to this.
    """
    if docstring.short_description:
        parts.append(docstring.short_description)
    if docstring.blank_after_short_description:
        parts.append("")
    if docstring.long_description:
        parts.append(docstring.long_description)
    if docstring.blank_after_long_description:
        parts.append("")
