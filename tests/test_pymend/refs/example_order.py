"""_summary_."""


def test1(param: int):
    """Short summary.
    Parameters
    ----------
    param : int
        description.

    Examples
    --------
    >>> test1(10)
    """
    pass


def test2(param: int):
    """Short summary.

    Long description

    Examples
    --------
    >>> test2(10)

    Parameters
    ----------
    param : int
        description.
    """
    pass


def test3(param: int):
    """Short summary.

    Long description

    Examples
    --------
    >>> test3(10)




    """
    pass


def test5(a: int) -> list[int]:
    """Stuff.

    Multi line long descritpion

    With an empty line

    Args:
        a (int): Short desc
            longer short desc

            some
            multi
            line
            long desc

    Returns:
        list[int]: Short desc.
            Longer short desc.

            Some multi
            line
            long description.


    Examples:
        >>> test5(10)

    Raises:
        ValueError: Description
            Short Desc

            Multi
            line
            long
    """
    if True:
        return [1]
    raise ValueError
