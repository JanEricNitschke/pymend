"""Unit tests for resolve_type_name helper."""

import pytest

from pymend.const import DEFAULT_TYPE
from pymend.docstring_info import ForceOption, resolve_type_name


class TestResolveTypeName:
    """Unit tests for the resolve_type_name helper."""

    @pytest.mark.parametrize(
        ("force_option", "types", "default", "expected"),
        [
            # FORCE: returns first non-None type, or default
            (ForceOption.FORCE, (), DEFAULT_TYPE, DEFAULT_TYPE),
            (ForceOption.FORCE, (None,), DEFAULT_TYPE, DEFAULT_TYPE),
            (ForceOption.FORCE, ("int",), DEFAULT_TYPE, "int"),
            (ForceOption.FORCE, (None, "str"), DEFAULT_TYPE, "str"),
            (ForceOption.FORCE, ("int", "str"), DEFAULT_TYPE, "int"),
            (ForceOption.FORCE, (None, None), DEFAULT_TYPE, DEFAULT_TYPE),
            (ForceOption.FORCE, ("int",), "custom", "int"),
            (ForceOption.FORCE, (None,), "custom", "custom"),
            # UNFORCE: always returns None
            (ForceOption.UNFORCE, (), DEFAULT_TYPE, None),
            (ForceOption.UNFORCE, (None,), DEFAULT_TYPE, None),
            (ForceOption.UNFORCE, ("int",), DEFAULT_TYPE, None),
            (ForceOption.UNFORCE, (None, "str"), DEFAULT_TYPE, None),
            (ForceOption.UNFORCE, ("int", "str"), DEFAULT_TYPE, None),
            # NOFORCE: returns first non-None type, or None (never default)
            (ForceOption.NOFORCE, (), DEFAULT_TYPE, None),
            (ForceOption.NOFORCE, (None,), DEFAULT_TYPE, None),
            (ForceOption.NOFORCE, ("int",), DEFAULT_TYPE, "int"),
            (ForceOption.NOFORCE, (None, "str"), DEFAULT_TYPE, "str"),
            (ForceOption.NOFORCE, ("int", "str"), DEFAULT_TYPE, "int"),
            (ForceOption.NOFORCE, (None, None), DEFAULT_TYPE, None),
        ],
    )
    def test_resolve_type_name(
        self,
        force_option: ForceOption,
        types: tuple[str | None, ...],
        default: str,
        expected: str | None,
    ) -> None:
        """Test resolve_type_name for all ForceOption modes."""
        assert resolve_type_name(force_option, *types, default=default) == expected
