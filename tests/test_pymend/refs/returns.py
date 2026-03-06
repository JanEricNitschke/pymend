"""_summary_."""


def my_func(param0, param01: int, param1: str = "Some value", param2: List[str] = {}):
    """_summary_.

    Args:
        param0 (_type_): _description_
        param01 (int): _description_
        param1 (str, optional): _description_. Defaults to "Some value".
        param2 (List[str], optional): _description_. Defaults to {}.
    """
    pass


def my_single_return_func1() -> str:
    """_summary_.

    Returns
    -------
    int
        Wrong
    """
    pass


def my_single_return_func2():
    """_summary_.

    Returns
    -------
    int
        Wrong
    """
    pass


def my_single_return_func3():
    pass


def my_single_return_func4():
    """Existing docstring."""
    pass


def my_single_return_func5() -> None:
    """Existing docstring."""
    pass


def my_single_return_func6() -> None:
    """Existing docstring."""
    return None


def my_single_return_func7():
    """Existing docstring."""
    return None


def my_func1(param0, param01: int):
    """_summary_.

    Args:
        param0 (_type_): _description_
        param01 (int): _description_
    """
    pass


def my_multi_return_func() -> Tuple[int, str, bool]:
    """_summary_.

    Returns
    -------
    x :
        Some integer
    y : str
        Some string
    z : bool
        Some bool
    """
    pass


def my_multi_return_func() -> Tuple[int, str, bool]:
    """_summary_.

    Returns
    -------
    x :
        Some integer
    y : str
        Some string
    """
    return x, y, z


def nested_function():
    """_summary_."""

    def nested_function1():
        """_summary_."""

        def nested_function2():
            """_summary_."""
            return 3


# R1: Mixed named/literal, single path — hits branch 2 (single doc entry),
#     type corrected from int to tuple[int, str].
def multi_return_mixed_single_path() -> tuple[int, str]:
    """_summary_.

    Returns
    -------
    x : int
        An integer.
    """
    return x, "hello"


# R2: Multiple same-length paths, all named — extends from 2 to 3.
#     Hint arity 3 matches body length 3, adds 'c'.
def multi_return_same_length_all_named() -> tuple[int, str, bool]:
    """_summary_.

    Returns
    -------
    a : int
        First.
    b : str
        Second.
    """
    if True:
        return a, b, c
    return a, b, d


# R3: Multiple same-length paths, mixed named/literal — no doc returns,
#     adds single return placeholder with type from signature.
def multi_return_mixed_no_doc() -> tuple[int, str]:
    """_summary_."""
    if True:
        return a, 2
    return 1, b


# R4: Different-length body tuples, hint + 3 doc entries.
#     No extension (body lengths not single). Reports length-2 mismatch.
def multi_return_diff_length_with_hint_and_doc() -> tuple[int, str, bool]:
    """_summary_.

    Returns
    -------
    a : int
        First.
    b : str
        Second.
    c : bool
        Third.
    """
    if True:
        return a, b
    return x, y, z


# R5: Different-length body tuples, hint, no doc returns —
#     adds single return placeholder.
def multi_return_diff_length_with_hint_no_doc() -> tuple[int, str]:
    """_summary_."""
    if True:
        return a, b
    return x, y, z


# R6: Different-length body tuples, no hint, 2 doc entries.
#     No extension (body lengths not single). Reports length-3 mismatch.
def multi_return_diff_length_no_hint_with_doc():
    """_summary_.

    Returns
    -------
    a : int
        First.
    b : str
        Second.
    """
    if True:
        return a, b
    return x, y, z


# R7: Different-length body tuples, no hint, no doc returns —
#     adds single return placeholder.
def multi_return_diff_length_no_hint_no_doc():
    """_summary_."""
    if True:
        return a, b
    return x, y, z


# R8: Doc order differs from body order — body order should win.
#     Doc says x, z, y but body always returns x, y, z.
def multi_return_body_reorders_doc() -> tuple[int, str, bool]:
    """_summary_.

    Returns
    -------
    x : int
        The x value.
    z : bool
        The z value.
    y : str
        The y value.
    """
    return x, y, z


# R9: Doc has a name that doesn't appear in body — doc name preserved.
#     Body returns (x, y) but doc calls position 1 "my_special".
def multi_return_doc_only_name() -> tuple[int, str]:
    """_summary_.

    Returns
    -------
    x : int
        The x value.
    my_special : str
        A special name.
    """
    return x, y


# R10: Body is inconsistent (name appears at different positions) —
#      doc order preserved as fallback.
def multi_return_inconsistent_body():
    """_summary_.

    Returns
    -------
    a : int
        First.
    b : str
        Second.
    """
    if True:
        return a, b
    return b, a


# R11: Extension case where doc names need reordering by body.
#      Doc has x, z but body returns (x, y, z) — extends to 3 and
#      reorders z to position 2, inserts y at position 1.
def multi_return_extension_reorder():
    """_summary_.

    Returns
    -------
    z : bool
        The z value.
    x : int
        The x value.
    """
    return x, y, z


# R12: Duplicate name in docstring — both entries preserved.
def multi_return_duplicate_doc_name() -> tuple[int, str]:
    """_summary_.

    Returns
    -------
    x : int
        First x.
    x : str
        Second x.
    """
    return x, y


# R13: Duplicate doc name with extension — body-only name fills gap.
def multi_return_duplicate_doc_name_extension():
    """_summary_.

    Returns
    -------
    x : int
        First x.
    x : str
        Second x.
    """
    return a, b, c


# R14: Doc name matches body name at a different position.
#      Doc says (b, a) but body consistently returns (a, b).
#      Body order should win: result is (a, b).
def multi_return_doc_swapped():
    """_summary_.

    Returns
    -------
    b : str
        The b value.
    a : int
        The a value.
    """
    return a, b


# R15: Single body path, doc has name not in body, body name at other
#      position would duplicate — duplicate guard prevents it.
#      Doc ["x"], body [("x", "y", "x_alias")], target 3.
#      x is consistent at pos 0, extends with y at 1 and x_alias at 2.
def multi_return_no_dup_on_extension():
    """_summary_.

    Returns
    -------
    x : int
        The x value.
    """
    return x, y, x_alias


# R16: All doc entries are unnamed (type-only), body has names.
#      The unnamed entries should hold their positions; body names
#      fill in where possible without displacing them.
def multi_return_unnamed_doc_with_body_names():
    """_summary_.

    Returns
    -------
    int
        An integer.
    str
        A string.
    """
    return x, y


# R17: Mix of named and unnamed doc entries, body has names for all.
#      The named entry should be placed by body-consistent position;
#      the unnamed entry holds a slot.
def multi_return_mixed_named_unnamed():
    """_summary_.

    Returns
    -------
    int
        An integer.
    y : str
        A string.
    bool
        A boolean.
    """
    return x, y, z


# R18: All unnamed doc entries, body extends beyond doc count.
#      Unnamed entries hold their slots; new body-only name fills the gap.
def multi_return_unnamed_doc_extension():
    """_summary_.

    Returns
    -------
    int
        An integer.
    str
        A string.
    """
    return x, y, z


# R19: No return section at all, body returns a tuple.
#      Should create return entries from scratch.
def multi_return_no_doc_section():
    """_summary_."""
    return x, y, z


# R19b: Same but with a type hint.
def multi_return_no_doc_section_with_hint() -> tuple[int, str, bool]:
    """_summary_."""
    return x, y, z


# R20: Multiple doc entries, some positions unnamed in both doc and body.
#      Body returns (x, <literal>, <literal>, y) — positions 1 and 2 have
#      no name from either source.  Doc has 4 unnamed entries.
#      Extension to 4 should fill x at 0, y at 3, and leave 1/2 unnamed.
def multi_return_mixed_unnamed_gaps():
    """_summary_.

    Returns
    -------
    int
        First value.
    str
        Second value.
    float
        Third value.
    bool
        Fourth value.
    """
    return x, 1, 2.0, y


# R21: Like R20 but body also extends beyond doc count.
#      Doc has 2 unnamed entries, body returns (x, <literal>, y) — 3 values.
#      Should extend to 3, with position 1 staying unnamed.
def multi_return_unnamed_gap_extension():
    """_summary_.

    Returns
    -------
    int
        First value.
    bool
        Last value.
    """
    return x, 1, y
