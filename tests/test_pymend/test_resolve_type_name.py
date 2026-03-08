"""Unit tests for resolve_type_name helper."""

import pytest
from _pytest.mark import ParameterSet

from pymend.const import DEFAULT_TYPE
from pymend.docstring_info import ForceOption, resolve_type_name


def _case(
    *,
    _id: str,
    force_option: ForceOption,
    doc_type: str | None,
    improved_types: tuple[str | None, ...],
    default: str,
    expected: str | None,
) -> ParameterSet:
    """Build a pytest.param with keyword arguments for readability."""
    return pytest.param(
        force_option,
        doc_type,
        improved_types,
        default,
        expected,
        id=_id,
    )


class TestResolveTypeName:
    """Unit tests for the resolve_type_name helper."""

    @pytest.mark.parametrize(
        ("force_option", "doc_type", "improved_types", "default", "expected"),
        [
            # ---- FORCE: best_improved > doc_type > default ----
            _case(
                _id="force-no_candidates-returns_default",
                force_option=ForceOption.FORCE,
                doc_type=None,
                improved_types=(),
                default=DEFAULT_TYPE,
                expected=DEFAULT_TYPE,
            ),
            _case(
                _id="force-only_doc_type-returns_doc_type",
                force_option=ForceOption.FORCE,
                doc_type="int",
                improved_types=(),
                default=DEFAULT_TYPE,
                expected="int",
            ),
            _case(
                _id="force-only_improved-returns_improved",
                force_option=ForceOption.FORCE,
                doc_type=None,
                improved_types=("str",),
                default=DEFAULT_TYPE,
                expected="str",
            ),
            _case(
                _id="force-both-improved_wins",
                force_option=ForceOption.FORCE,
                doc_type="int",
                improved_types=("str",),
                default=DEFAULT_TYPE,
                expected="str",
            ),
            _case(
                _id="force-improved_none_then_value-picks_value",
                force_option=ForceOption.FORCE,
                doc_type=None,
                improved_types=(None, "str"),
                default=DEFAULT_TYPE,
                expected="str",
            ),
            _case(
                _id="force-all_none-returns_default",
                force_option=ForceOption.FORCE,
                doc_type=None,
                improved_types=(None, None),
                default=DEFAULT_TYPE,
                expected=DEFAULT_TYPE,
            ),
            _case(
                _id="force-custom_default-returns_custom",
                force_option=ForceOption.FORCE,
                doc_type=None,
                improved_types=(),
                default="custom",
                expected="custom",
            ),
            _case(
                _id="force-improved_with_custom_default-returns_improved",
                force_option=ForceOption.FORCE,
                doc_type=None,
                improved_types=("int",),
                default="custom",
                expected="int",
            ),
            # ---- UNFORCE: always None ----
            _case(
                _id="unforce-no_candidates-returns_none",
                force_option=ForceOption.UNFORCE,
                doc_type=None,
                improved_types=(),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            _case(
                _id="unforce-doc_type_present-returns_none",
                force_option=ForceOption.UNFORCE,
                doc_type="int",
                improved_types=(),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            _case(
                _id="unforce-improved_present-returns_none",
                force_option=ForceOption.UNFORCE,
                doc_type=None,
                improved_types=("str",),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            _case(
                _id="unforce-both_present-returns_none",
                force_option=ForceOption.UNFORCE,
                doc_type="int",
                improved_types=("str",),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            # ---- NOFORCE: correct existing, never add missing ----
            _case(
                _id="noforce-no_doc_type_no_improved-returns_none",
                force_option=ForceOption.NOFORCE,
                doc_type=None,
                improved_types=(),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            _case(
                _id="noforce-no_doc_type_with_improved-returns_none",
                force_option=ForceOption.NOFORCE,
                doc_type=None,
                improved_types=("str",),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            _case(
                _id="noforce-no_doc_type_improved_mixed-returns_none",
                force_option=ForceOption.NOFORCE,
                doc_type=None,
                improved_types=(None, "str"),
                default=DEFAULT_TYPE,
                expected=None,
            ),
            _case(
                _id="noforce-doc_type_no_improved-preserves_doc_type",
                force_option=ForceOption.NOFORCE,
                doc_type="int",
                improved_types=(),
                default=DEFAULT_TYPE,
                expected="int",
            ),
            _case(
                _id="noforce-doc_type_improved_none-preserves_doc_type",
                force_option=ForceOption.NOFORCE,
                doc_type="int",
                improved_types=(None,),
                default=DEFAULT_TYPE,
                expected="int",
            ),
            _case(
                _id="noforce-doc_type_with_improved-improved_wins",
                force_option=ForceOption.NOFORCE,
                doc_type="wrong",
                improved_types=("int",),
                default=DEFAULT_TYPE,
                expected="int",
            ),
            _case(
                _id="noforce-doc_type_improved_mixed-improved_wins",
                force_option=ForceOption.NOFORCE,
                doc_type="old",
                improved_types=(None, "new"),
                default=DEFAULT_TYPE,
                expected="new",
            ),
        ],
    )
    def test_resolve_type_name(
        self,
        force_option: ForceOption,
        doc_type: str | None,
        improved_types: tuple[str | None, ...],
        default: str,
        expected: str | None,
    ) -> None:
        """Test resolve_type_name for all ForceOption modes."""
        assert (
            resolve_type_name(
                force_option,
                doc_type=doc_type,
                improved_types=improved_types,
                default=default,
            )
            == expected
        )
