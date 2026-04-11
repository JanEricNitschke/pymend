"""Constant value used across pymend."""

import re
from enum import Enum


class OutputMode(Enum):
    """Output mode for pymend."""

    WRITE = "write"
    DIFF = "diff"
    CHECK_ONLY = "check-only"


DEFAULT_EXCLUDES = re.compile(
    r"/(\.direnv|\.eggs|\.git|\.hg|\.ipynb_checkpoints|\.mypy_cache|\.nox|\.pytest_cache|\.ruff_cache|\.tox|\.svn|\.venv|\.vscode|__pypackages__|_build|buck-out|build|dist|venv)/"  # pylint: disable=line-too-long
)
DEFAULT_DESCRIPTION = "_description_"
DEFAULT_TYPE = "_type_"
DEFAULT_SUMMARY = "_summary_."
DEFAULT_EXCEPTION = "__UnknownError__"

ARG_TYPE_SET = "Parameter had type despite `force-arg-types=unforce` being set."
RETURN_TYPE_SET = (
    "Return type was specified despite `force-return-type=unforce` being set."
)
ATTRIBUTE_TYPE_SET = (
    "Attribute had type despite `force-attribute-types=unforce` being set."
)
