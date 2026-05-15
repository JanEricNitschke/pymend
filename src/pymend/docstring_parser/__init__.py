"""Parse docstrings as per Sphinx notation."""

from .base_parser import compose, parse
from .common import (
    Docstring,
    DocstringDeprecated,
    DocstringExample,
    DocstringMeta,
    DocstringParam,
    DocstringParserModule,
    DocstringRaises,
    DocstringReturns,
    DocstringReturnsBase,
    DocstringStyle,
    DocstringYields,
    ParseError,
    RenderingStyle,
)

Style = DocstringStyle  # backwards compatibility

__all__ = [
    "Docstring",
    "DocstringDeprecated",
    "DocstringExample",
    "DocstringMeta",
    "DocstringParam",
    "DocstringParserModule",
    "DocstringRaises",
    "DocstringReturns",
    "DocstringReturnsBase",
    "DocstringStyle",
    "DocstringYields",
    "ParseError",
    "RenderingStyle",
    "Style",
    "compose",
    "parse",
]
