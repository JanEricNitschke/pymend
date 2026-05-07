"""Constant value used across pymend."""

import builtins
import re
import sys
from enum import Enum
from functools import lru_cache

from typing_extensions import override

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        """Simulate StrEnum __str__ behaviour in 3.10."""

        @override
        def __str__(self) -> str:
            """Emulate the __str__ behaviour of a StrEnum."""
            return str(self.value)


class OutputMode(StrEnum):
    """Output mode for pymend."""

    WRITE = "write"
    DIFF = "diff"
    CHECK_ONLY = "check-only"


class ForceOption(StrEnum):
    """Three-valued option for type-hint enforcement.

    Attributes
    ----------
    FORCE : str
        Actively enforce the existence of type information.
    UNFORCE : str
        Actively enforce the lack of type information (strip).
    NOFORCE : str
        Don't enforce either way (preserve as-is).
    """

    FORCE = "force"
    UNFORCE = "unforce"
    NOFORCE = "noforce"


class RaisesForceMode(StrEnum):
    """Three-valued option for raises section enforcement.

    Attributes
    ----------
    OFF : str
        Don't enforce raises section.
    PER_TYPE : str
        Each exception type must be documented at least once.
    PER_SITE : str
        Each raise site must be documented (one entry per raise).
    """

    OFF = "off"
    PER_TYPE = "per-type"
    PER_SITE = "per-site"


FORCE_ARG_TYPES = "force_arg_types"
FORCE_RETURN_TYPE = "force_return_type"
FORCE_ATTRIBUTE_TYPES = "force_attribute_types"
FORCE_RAISES = "force_raises"
MODE = "mode"

FORCE_OPTION_KEYS = frozenset(
    {FORCE_ARG_TYPES, FORCE_RETURN_TYPE, FORCE_ATTRIBUTE_TYPES}
)

OPTIONS_NOT_IN_PYPROJECT = frozenset(
    {"verbose", "quiet", "config", "src", "version", "help"}
)


DEFAULT_EXCLUDES = re.compile(
    r"/(\.direnv|\.eggs|\.git|\.hg|\.ipynb_checkpoints|\.mypy_cache|\.nox|\.pytest_cache|\.ruff_cache|\.tox|\.svn|\.venv|\.vscode|__pypackages__|_build|buck-out|build|dist|venv)/"  # pylint: disable=line-too-long
)
DEFAULT_DESCRIPTION = "_description_"
DEFAULT_TYPE = "_type_"
DEFAULT_SUMMARY = "_summary_."
DEFAULT_EXCEPTION = "__UnknownError__"

REPORT_URL = "https://github.com/JanEricNitschke/pymend/issues"
INTERNAL_ERROR_TAG = "INTERNAL ERROR"
INTERNAL_FAILURE_EXIT_CODE = 123

ARG_TYPE_SET = "Parameter had type despite `force-arg-types=unforce` being set."
RETURN_TYPE_SET = (
    "Return type was specified despite `force-return-type=unforce` being set."
)
ATTRIBUTE_TYPE_SET = (
    "Attribute had type despite `force-attribute-types=unforce` being set."
)

PASCAL_CASE_REGEX = r"^(?:[A-Z][a-z]*)+$"


def is_exception_name(name: str) -> bool:
    """Check whether *name* looks like an exception class name.

    For dotted names (e.g. ``click.BadUsage``) every part except the
    last must be a valid Python identifier and the final part must
    match :pydata:`PASCAL_CASE_REGEX`.  For simple names the whole
    string must match the regex.

    Parameters
    ----------
    name : str
        The name to check.

    Returns
    -------
    bool
        Whether *name* is a valid exception name.
    """
    parts = name.split(".")
    if len(parts) == 1:
        return bool(re.match(PASCAL_CASE_REGEX, name))
    return all(p.isidentifier() for p in parts[:-1]) and bool(
        re.match(PASCAL_CASE_REGEX, parts[-1])
    )


def internal_error_message(description: str, *, hint: str = "") -> str:
    """Format a consistent internal error message.

    Parameters
    ----------
    description : str
        What went wrong.
    hint : str
        Optional extra context (e.g. a log file path). (Default value = '')

    Returns
    -------
    str
        The formatted message.
    """
    msg = f"{INTERNAL_ERROR_TAG}: {description} Please report a bug on {REPORT_URL}."
    if hint:
        msg += f" {hint}"
    return msg


@lru_cache(maxsize=1)
def builtin_exception_ancestors() -> dict[str, frozenset[str]]:
    """Build a mapping of builtin exception names to their ancestor names.

    Each key is the name of a builtin exception class. The value is a
    frozenset of all ancestor class names (including the class itself)
    that are subclasses of `BaseException`.

    This is computed lazily and cached so it automatically reflects the
    Python version actually running pymend.

    Returns
    -------
    dict[str, frozenset[str]]
        Mapping of builtin exception names to their ancestor names
    """
    result: dict[str, frozenset[str]] = {}
    for name in dir(builtins):
        obj = getattr(builtins, name)
        if isinstance(obj, type) and issubclass(obj, BaseException):
            ancestors = frozenset(
                cls.__name__ for cls in obj.__mro__ if issubclass(cls, BaseException)
            )
            result[name] = ancestors
    return result


def is_exception_caught_by(exc_name: str, caught_names: frozenset[str]) -> bool:
    """Check whether *exc_name* would be caught by any of *caught_names*.

    Uses the builtin exception hierarchy so that `except OSError`
    is recognised as catching `FileNotFoundError`, etc.  User-defined
    exceptions that are not in the builtin hierarchy are only matched
    by exact name, `BaseException`, or bare `except`.

    Parameters
    ----------
    exc_name : str
        Name of the thrown exception
    caught_names : frozenset[str]
        Names of all the caught exceptions

    Returns
    -------
    bool
        Whether the thrown exception is caught by any handler
    """
    if "BaseException" in caught_names:
        return True
    ancestors = builtin_exception_ancestors().get(exc_name)
    if ancestors is not None:
        return bool(ancestors & caught_names)
    return exc_name in caught_names


def is_exception_group_type(name: str) -> bool:
    """Check whether *name* refers to an exception group class.

    Returns `True` for `BaseExceptionGroup`, `ExceptionGroup`, and
    any builtin exception whose ancestors include `BaseExceptionGroup`.
    Also returns `True` for user-defined names ending with `Group`
    as a best-effort heuristic.
    """
    ancestors = builtin_exception_ancestors().get(name)
    if ancestors is not None:
        return "BaseExceptionGroup" in ancestors
    return name.endswith("Group")
