"""Unit tests for the ForceDocstringsMode enum and DocstringInfo._should_force_docstring."""

import pytest

from pymend.docstring_info import DocstringInfo, ForceDocstringsMode


def _make_info(name: str, docstring: str = "") -> DocstringInfo:
    """Build a DocstringInfo with just enough fields for the force-mode probe."""
    return DocstringInfo(
        name=name,
        docstring=docstring,
        lines=(1, None),
        modifier="",
        issues=[],
        had_docstring=bool(docstring),
    )


class TestIsPrivate:
    """Tests for DocstringInfo._is_private."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("foo", False),
            ("Foo", False),
            ("module.public_fn", False),
            ("Foo.method", False),
            ("_private", True),
            ("__init__", True),
            ("Foo._private_method", True),
            ("Foo.__dunder__", True),
            ("a.b.c._d", True),
        ],
    )
    def test_is_private(self, name: str, expected: bool) -> None:
        info = _make_info(name)
        # pylint: disable=protected-access
        assert info._is_private() is expected


class TestShouldForceDocstring:
    """Tests for DocstringInfo._should_force_docstring."""

    @pytest.mark.parametrize(
        ("mode", "name", "expected"),
        [
            (ForceDocstringsMode.OFF, "public_fn", False),
            (ForceDocstringsMode.OFF, "_private_fn", False),
            (ForceDocstringsMode.ALL, "public_fn", True),
            (ForceDocstringsMode.ALL, "_private_fn", True),
            (ForceDocstringsMode.PUBLIC_ONLY, "public_fn", True),
            (ForceDocstringsMode.PUBLIC_ONLY, "_private_fn", False),
            (ForceDocstringsMode.PUBLIC_ONLY, "Foo.public_method", True),
            (ForceDocstringsMode.PUBLIC_ONLY, "Foo._private_method", False),
            (ForceDocstringsMode.PUBLIC_ONLY, "Foo.__init__", False),
        ],
    )
    def test_should_force_docstring(
        self, mode: ForceDocstringsMode, name: str, expected: bool,
    ) -> None:
        info = _make_info(name)
        # pylint: disable=protected-access
        assert info._should_force_docstring(mode) is expected
