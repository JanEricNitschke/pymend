"""Google-style return test cases."""


# G1: All doc entries are unnamed (type-only), body has names.
#     The unnamed entries should hold their positions; body names
#     fill in where possible without displacing them.
def multi_return_unnamed_doc_with_body_names():
    """_summary_.

    Returns:
        int: An integer.
        str: A string.
    """
    return x, y


# G2: Mix of named and unnamed doc entries, body has names for all.
#     The named entry should be placed by body-consistent position;
#     the unnamed entry holds a slot.
def multi_return_mixed_named_unnamed():
    """_summary_.

    Returns:
        int: An integer.
        y (str): A string.
        bool: A boolean.
    """
    return x, y, z


# G3: Doc order differs from body order — body order should win.
#     Doc says x, z, y but body always returns x, y, z.
def multi_return_body_reorders_doc() -> tuple[int, str, bool]:
    """_summary_.

    Returns:
        x (int): The x value.
        z (bool): The z value.
        y (str): The y value.
    """
    return x, y, z


# G4: Doc has a name that doesn't appear in body — doc name preserved.
#     Body returns (x, y) but doc calls position 1 "my_special".
def multi_return_doc_only_name() -> tuple[int, str]:
    """_summary_.

    Returns:
        x (int): The x value.
        my_special (str): A special name.
    """
    return x, y


# G5: Body is inconsistent (name appears at different positions) —
#     doc order preserved as fallback.
def multi_return_inconsistent_body():
    """_summary_.

    Returns:
        a (int): First.
        b (str): Second.
    """
    if True:
        return a, b
    return b, a


# G6: No return section at all, body returns a tuple.
#     Should create return entries from scratch.
def multi_return_no_doc_section():
    """_summary_."""
    return x, y, z


# G6b: Same but with a type hint.
def multi_return_no_doc_section_with_hint() -> tuple[int, str, bool]:
    """_summary_."""
    return x, y, z


# G7: Multiple doc entries, some positions unnamed in both doc and body.
#     Body returns (x, <literal>, <literal>, y) — positions 1 and 2 have
#     no name from either source.  Doc has 4 unnamed entries.
def multi_return_mixed_unnamed_gaps():
    """_summary_.

    Returns:
        int: First value.
        str: Second value.
        float: Third value.
        bool: Fourth value.
    """
    return x, 1, 2.0, y


# G8: Like G7 but body extends beyond doc count.
#     Doc has 2 unnamed entries, body returns (x, <literal>, y) — 3 values.
def multi_return_unnamed_gap_extension():
    """_summary_.

    Returns:
        int: First value.
        bool: Last value.
    """
    return x, 1, y
