"""Test for raises handling with different modes."""


def no_docstring_multiple_raises(x: int):
    if x < 0:
        raise ValueError("x is negative")
    if x > 100:
        raise ValueError("x is too large")


def has_docstring_multiple_raises(x: int):
    """Process x with multiple raises.

    Parameters
    ----------
    x : int
        Input value.

    Raises
    ------
    ValueError
        If x is out of range.
    """
    if x < 0:
        raise ValueError("x is negative")
    if x > 100:
        raise ValueError("x is too large")


def no_docstring_unique_raises(x: int):
    if x < 0:
        raise ValueError("x is negative")
    raise TypeError("x must be int")


def has_docstring_unique_raises(x: int):
    """Process x with unique raises.

    Parameters
    ----------
    x : int
        Input value.

    Raises
    ------
    ValueError
        If x is negative.
    TypeError
        If x is not int.
    """
    if x < 0:
        raise ValueError("x is negative")
    raise TypeError("x must be int")


def raises():
    """_summary_.

    Raises
    ------
    ValueError
        _description_
    TypeError
        _description_
    SpecificError
        _description_
    """
    my_exceptions = [ValueError, TypeError]
    raise ValueError
    raise KeyError
    raise TypeError(msg)
    raise ValueError
    raise
    raise my_exceptions[0]


def duplicate_in_docstring(x: int):
    """Test case with duplicate exception in docstring.

    Parameters
    ----------
    x : int
        Input value.

    Raises
    ------
    ValueError
        If x is negative.
    ValueError
        If x is too large.
    """
    if x < 0:
        raise ValueError("x is negative")
    if x > 100:
        raise ValueError("x is too large")
    raise
