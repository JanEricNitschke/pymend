"""Unit tests for helper functions in pymend.docstring_info."""

import ast

import pytest

from pymend.docstring_info import (
    FixedLengthTuple,
    NonTupleTypeHint,
    NoTypeHint,
    VariableLengthTuple,
    _classify_type_hint,  # pyright: ignore[reportPrivateUsage]
    _merge_return_names,  # pyright: ignore[reportPrivateUsage]
    _split_generator_args,  # pyright: ignore[reportPrivateUsage]
)
from pymend.file_parser import AstAnalyzer

# ---------------------------------------------------------------------------
# _split_generator_args
# ---------------------------------------------------------------------------


class TestSplitGeneratorArgs:
    """Tests for _split_generator_args."""

    @pytest.mark.parametrize(
        ("type_str", "expected"),
        [
            pytest.param(
                "Generator[int, float, str]",
                ("int", "float", "str"),
                id="simple",
            ),
            pytest.param(
                "Generator[list[int], None, tuple[str, int]]",
                ("list[int]", "None", "tuple[str, int]"),
                id="complex_nested",
            ),
            pytest.param(
                "Generator[dict[str, list[tuple[int, int]]], None, str]",
                ("dict[str, list[tuple[int, int]]]", "None", "str"),
                id="deeply_nested",
            ),
            pytest.param(
                "Generator[int, str]",
                None,
                id="wrong_arity_2",
            ),
            pytest.param(
                "Generator[int, str, bool, float]",
                None,
                id="wrong_arity_4",
            ),
            pytest.param(
                "Iterator[str]",
                None,
                id="not_generator",
            ),
            pytest.param(
                "Generator[list[int, str]",
                None,
                id="malformed_unbalanced",
            ),
            pytest.param(
                "Generator[int], str, bool]",
                None,
                id="malformed_extra_close",
            ),
            pytest.param(
                "Generator[]",
                None,
                id="empty_args",
            ),
        ],
    )
    def test_split_generator_args(
        self, type_str: str, expected: tuple[str, str, str] | None
    ) -> None:
        """Verify extraction of Generator type arguments."""
        assert _split_generator_args(type_str) == expected


# ---------------------------------------------------------------------------
# _classify_type_hint
# ---------------------------------------------------------------------------


class TestClassifyTypeHint:
    """Tests for _classify_type_hint."""

    def test_no_hint(self) -> None:
        """None input means no annotation."""
        assert isinstance(_classify_type_hint(None), NoTypeHint)

    def test_non_tuple(self) -> None:
        """Plain type like 'str' is not a tuple."""
        assert isinstance(_classify_type_hint("str"), NonTupleTypeHint)

    def test_fixed_tuple_lower(self) -> None:
        """Lowercase tuple with 2 elements."""
        result = _classify_type_hint("tuple[int, str]")
        assert isinstance(result, FixedLengthTuple)
        assert result.arity == 2

    def test_fixed_tuple_upper(self) -> None:
        """Uppercase Tuple with 3 elements."""
        result = _classify_type_hint("Tuple[int, str, bool]")
        assert isinstance(result, FixedLengthTuple)
        assert result.arity == 3

    def test_variable_tuple(self) -> None:
        """tuple[int, ...] is a variable-length tuple."""
        assert isinstance(_classify_type_hint("tuple[int, ...]"), VariableLengthTuple)

    def test_nested_tuple(self) -> None:
        """Nested types inside the tuple."""
        result = _classify_type_hint("tuple[list[int], dict[str, bool]]")
        assert isinstance(result, FixedLengthTuple)
        assert result.arity == 2

    def test_malformed(self) -> None:
        """Unbalanced brackets treated as non-tuple."""
        assert isinstance(_classify_type_hint("tuple[int, str"), NonTupleTypeHint)


# ---------------------------------------------------------------------------
# AstAnalyzer.get_ids_from_tuple
# ---------------------------------------------------------------------------


class TestGetIdsFromTuple:
    """Tests for AstAnalyzer.get_ids_from_tuple."""

    @staticmethod
    def _tuple_elts(source: str) -> list[ast.expr]:
        """Parse ``return <source>`` and return the tuple element nodes."""
        tree = ast.parse(f"return {source}")
        ret = tree.body[0]
        assert isinstance(ret, ast.Return)
        assert isinstance(ret.value, ast.Tuple)
        return ret.value.elts

    def test_all_named(self) -> None:
        """All Name nodes produce their ids."""
        nodes = self._tuple_elts("a, b")
        assert AstAnalyzer.get_ids_from_tuple(nodes) == ("a", "b")

    def test_mixed(self) -> None:
        """Name + Constant produces id + None."""
        nodes = self._tuple_elts("a, 2")
        assert AstAnalyzer.get_ids_from_tuple(nodes) == ("a", None)

    def test_all_literal(self) -> None:
        """All Constant nodes produce all None."""
        nodes = self._tuple_elts("1, 2")
        assert AstAnalyzer.get_ids_from_tuple(nodes) == (None, None)


# ---------------------------------------------------------------------------
# _merge_return_names — non-extension (target_length == len(doc_names))
# ---------------------------------------------------------------------------


class TestMergeReturnNames:
    """Tests for _merge_return_names."""

    def test_docstring_priority(self) -> None:
        """Docstring names win over body names at the same position."""
        result = _merge_return_names(
            body_returns=[("x", "y")], doc_names=["a", None], target_length=2
        )
        assert result == ("a", "y")

    def test_most_common(self) -> None:
        """Most frequent body name at each position wins."""
        result = _merge_return_names(
            body_returns=[("x", "y"), ("x", "z"), ("w", "y")],
            doc_names=[None, None],
            target_length=2,
        )
        assert result == ("x", "y")

    def test_first_wins_tie(self) -> None:
        """On ties, first occurrence (by insertion order) wins."""
        result = _merge_return_names(
            body_returns=[("a", "x"), ("b", "x")],
            doc_names=[None, None],
            target_length=2,
        )
        assert result == ("a", "x")

    def test_no_matching_length(self) -> None:
        """Body tuples of wrong length are ignored."""
        result = _merge_return_names(
            body_returns=[("a", "b", "c")], doc_names=[None, None], target_length=2
        )
        assert result == (None, None)

    def test_empty_body(self) -> None:
        """No body tuples returns doc names as-is."""
        result = _merge_return_names(
            body_returns=[], doc_names=["a", "b"], target_length=2
        )
        assert result == ("a", "b")

    def test_swapped_order(self) -> None:
        """Order is preferred from body."""
        result = _merge_return_names(
            body_returns=[("a", "b")], doc_names=["b", "a"], target_length=2
        )
        assert result == ("a", "b")

    def test_swapped_order_tie(self) -> None:
        """Order is preferred from body, first occurrence breaks tie."""
        result = _merge_return_names(
            body_returns=[("a", "b", "c"), ("a", "b", "x")],
            doc_names=["a", "c", "x"],
            target_length=3,
        )
        assert result == ("a", "x", "c")


# ---------------------------------------------------------------------------
# _merge_return_names — extension (target_length > len(doc_names))
# ---------------------------------------------------------------------------


class TestMergeReturnNamesExtension:
    """Tests for _merge_return_names with target_length > len(doc_names)."""

    def test_extend_with_alignment(self) -> None:
        """Doc names aligned to unambiguous body positions, gap filled."""
        # body: (x, y, z), doc: [x, z] → x@0, z@2, y fills pos 1
        result = _merge_return_names(
            body_returns=[("x", "y", "z")], doc_names=["x", "z"], target_length=3
        )
        assert result == ("x", "y", "z")

    def test_extend_most_common_fill(self) -> None:
        """Multiple body tuples; gap position filled by most common name."""
        # body: (a,b,c) and (a,b,d), doc: [a, b] → a@0, b@1, pos 2 = c (first wins)
        result = _merge_return_names(
            body_returns=[("a", "b", "d"), ("a", "b", "c"), ("a", "b", "c")],
            doc_names=["a", "b"],
            target_length=3,
        )
        assert result == ("a", "b", "c")

    def test_extend_most_first_fill(self) -> None:
        """Multiple body tuples; gap position filled by most first name if tie ."""
        # body: (a,b,c) and (a,b,d), doc: [a, b] → a@0, b@1, pos 2 = c (first wins)
        result = _merge_return_names(
            body_returns=[("a", "b", "c"), ("a", "b", "d")],
            doc_names=["a", "b"],
            target_length=3,
        )
        assert result == ("a", "b", "c")

    def test_extend_unmatched_doc_name(self) -> None:
        """Doc name not in body fills first available slot."""
        # body: (x, y, z), doc: [x, q] → x@0 (unambiguous), q→pos 1 (first free)
        result = _merge_return_names(
            body_returns=[("x", "y", "z")], doc_names=["x", "q"], target_length=3
        )
        assert result == ("x", "q", "z")

    def test_extend_no_matching_body(self) -> None:
        """No body tuples of target length; doc names placed in order, rest None."""
        result = _merge_return_names(
            body_returns=[("a", "b")], doc_names=["x", "z"], target_length=3
        )
        assert result == ("x", "z", None)

    def test_extend_ambiguous_doc_name(self) -> None:
        """Doc name appearing at multiple body positions goes to first free slot."""
        # body: (a, b, a), doc: [a] → "a" appears at pos 0 and 2, ambiguous
        # → fills pos 0 (first free), rest from body
        result = _merge_return_names(
            body_returns=[("z", "y", "x"), ("x", "y", "z")],
            doc_names=["x"],
            target_length=3,
        )
        assert result == ("x", "y", "z")

    def test_extend_ambiguous_doc_name_duplicated(self) -> None:
        """If a name occurs multiple time in one return statement it can occur multiple times in the docstring."""  # noqa: E501
        # body: (a, b, a), doc: [a] → "a" appears at pos 0 and 2, ambiguous
        # → fills pos 0 (first free), rest from body
        result = _merge_return_names(
            body_returns=[("a", "b", "a")], doc_names=["a"], target_length=3
        )
        assert result == ("a", "b", "a")
