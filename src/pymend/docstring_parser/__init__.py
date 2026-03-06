"""Parse docstrings as per Sphinx notation."""

from .base_parser import compose, parse
from .common import (
    Docstring,
    DocstringDeprecated,
    DocstringExample,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringReturnsBase,
    DocstringStyle,
    DocstringYields,
    ParseError,
    RenderingStyle,
)
from .util import combine_docstrings

Style = DocstringStyle  # backwards compatibility

__all__ = [
    "Docstring",
    "DocstringDeprecated",
    "DocstringExample",
    "DocstringMeta",
    "DocstringParam",
    "DocstringRaises",
    "DocstringReturns",
    "DocstringReturnsBase",
    "DocstringStyle",
    "DocstringYields",
    "ParseError",
    "RenderingStyle",
    "Style",
    "combine_docstrings",
    "compose",
    "parse",
]
