"""Common methods for parsing."""

import enum
from collections import UserDict
from dataclasses import dataclass
from typing import Protocol, TypeAlias, TypeVar, overload

from typing_extensions import override

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
class DocstringReturnsBase(DocstringMeta):
    """Base class for :returns and :yields metadata."""

    type_name: str | None
    name: str | None = None


@dataclass
class DocstringReturns(DocstringReturnsBase):
    """DocstringMeta symbolizing :returns metadata."""


@dataclass
class DocstringYields(DocstringReturnsBase):
    """DocstringMeta symbolizing :yields metadata."""


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
        section_titles : KeyReturnDict[str, str] | None
            Dictionary mapping a section ke to its title (Default value = None)
        """
        self.short_description: str | None = None
        self.long_description: str | None = None
        self.blank_after_short_description: bool = False
        self.blank_after_long_description: bool = False
        self.meta: list[DocstringMeta] = []
        self.style: DocstringStyle | None = style
        self.section_titles: KeyReturnDict[str, str] = section_titles or KeyReturnDict()
        self.return_type_annotation: str | None = None
        self.yield_type_annotation: str | None = None

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

    @override
    def __str__(self) -> str:
        """Return string representation useful for debugging."""
        return (
            f"Docstring(short_description={self.short_description!r}, "
            f"long_description={self.long_description!r}, "
            f"meta={self.meta!r})"
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
            (item for item in self.meta if isinstance(item, DocstringYields)),
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


@overload
def collapse_entries(
    entries: list[DocstringReturns],
    type_annotation: str | None,
) -> list[DocstringReturns]: ...


@overload
def collapse_entries(
    entries: list[DocstringYields],
    type_annotation: str | None,
) -> list[DocstringYields]: ...


def collapse_entries(
    entries: list[DocstringReturns] | list[DocstringYields],
    type_annotation: str | None,
) -> list[DocstringReturns] | list[DocstringYields]:
    """Collapse multiple return/yield entries into a single entry.

    Styles like Google, reST, and Epydoc do not support multiple individual
    return/yield entries. When multiple entries exist (e.g., from parsing
    a tuple return documented as individual types), they are collapsed into
    a single entry.

    Descriptions are joined with plain newlines. Each style's compose
    function handles indentation via its own ``splitlines()`` logic.

    Parameters
    ----------
    entries : list[DocstringReturns] | list[DocstringYields]
        List of return or yield entries from the docstring.
    type_annotation : str | None
        The full type annotation from the function signature
        (e.g., ``tuple[int, str]``). Used as the type for the collapsed entry
        if available.

    Returns
    -------
    list[DocstringReturns] | list[DocstringYields]
        The original list if it has 0 or 1 entries, otherwise a single-element
        list with the collapsed entry.
    """
    if len(entries) <= 1:
        return entries
    if type_annotation:
        type_name = type_annotation
    elif all(e.type_name for e in entries):
        type_name = f"tuple[{', '.join(e.type_name for e in entries if e.type_name)}]"
    else:
        type_name = None
    descriptions = [e.description for e in entries if e.description]
    description = "\n".join(descriptions) if descriptions else None
    if isinstance(entries[0], DocstringYields):
        return [
            DocstringYields(
                args=["yields"],
                description=description,
                type_name=type_name,
            )
        ]
    return [
        DocstringReturns(
            args=["returns"],
            description=description,
            type_name=type_name,
        )
    ]


def collapse_meta(
    docstring: Docstring,
) -> list[DocstringMeta]:
    """Build a new meta list with multiple returns/yields collapsed.

    Replaces all ``DocstringReturns`` entries with a single collapsed entry,
    and all ``DocstringYields`` entries with a single collapsed entry.
    The collapsed entries are placed where the first original entry was.
    All other meta items are kept as-is in their original order.

    Parameters
    ----------
    docstring : Docstring
        The docstring whose meta list should be collapsed.

    Returns
    -------
    list[DocstringMeta]
        A new meta list with collapsed return/yield entries.
    """
    collapsed_returns = collapse_entries(
        docstring.many_returns,
        docstring.return_type_annotation,
    )
    collapsed_yields = collapse_entries(
        docstring.many_yields,
        docstring.yield_type_annotation,
    )
    returns_inserted = False
    yields_inserted = False
    result: list[DocstringMeta] = []
    for item in docstring.meta:
        if isinstance(item, DocstringReturns):
            if not returns_inserted:
                returns_inserted = True
                result.extend(collapsed_returns)
        elif isinstance(item, DocstringYields):
            if not yields_inserted:
                yields_inserted = True
                result.extend(collapsed_yields)
        else:
            result.append(item)
    return result


class DocstringParserModule(Protocol):
    """Protocol for docstring parse modules."""

    def parse(self, text: str | None) -> Docstring:
        """Parse the docstring into its components.

        Parameters
        ----------
        text : str | None
            docstring text

        Returns
        -------
        Docstring
            parsed docstring
        """
        ...

    def compose(
        self,
        docstring: Docstring,
        rendering_style: RenderingStyle = RenderingStyle.COMPACT,
        indent: str = "    ",
    ) -> str:
        """Render a parsed docstring into docstring text.

        Parameters
        ----------
        docstring : Docstring
            parsed docstring representation
        rendering_style : RenderingStyle
            the style to render docstrings (Default value = RenderingStyle.COMPACT)
        indent : str
            the characters used as indentation in the
            docstring string (Default value = '    ')

        Returns
        -------
        str
            docstring text
        """
        ...
