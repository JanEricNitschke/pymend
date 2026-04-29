"""_summary_."""

def test_examples_after_common_sections(a: int) -> list[int]:
    """Stuff.

    Examples
    --------
    >>> test_examples_after_common_sections(10)

    >>> test_examples_after_common_sections(20)

    Parameters
    ----------
    a : int
        Short desc
        longer short desc

        some
        multi
        line
        long desc

    Returns
    -------
    list[int]
        Short desc.
        Longer short desc.

        Some multi
        line
        long description.
    """

def t(a: int) -> list[int]:
    """Stuff.

    Parameters
    ----------
    a : int
        Short desc
        longer short desc

        some
        multi
        line
        long desc

    Returns
    -------
    list[int]
        Short desc.
        Longer short desc.

        Some multi
        line
        long description.

    Examples
    --------
    >>> test_examples_after_miscelaneous(10)

    >>> test_examples_after_miscelaneous(20)

    Raises
    ------
    ValueError
        Description
        Short Desc

        Multi
        line
        long

    Notes
    -----
    Some notes here.
    """
    if True:
        return [1]
    raise ValueError
