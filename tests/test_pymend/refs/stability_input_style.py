"""Module with docstrings in all four styles for stability testing."""


def rest_func(first: str, second: int = 0) -> int:
    """Do something useful with reST style.

    :param first: the first argument
    :param second: the second argument
    :returns: the result value
    :raises KeyError: when key is not found
    """
    return len(first) + second


def google_func(first: str, second: int = 0) -> int:
    """Do something useful with Google style.

    Args:
        first: the first argument
        second: the second argument

    Returns:
        the result value

    Raises:
        KeyError: when key is not found
    """
    return len(first) + second


def numpy_func(first: str, second: int = 0) -> int:
    """Do something useful with NumPy style.

    Parameters
    ----------
    first : str
        the first argument
    second : int, optional
        the second argument

    Returns
    -------
    int
        the result value

    Raises
    ------
    KeyError
        when key is not found
    """
    return len(first) + second


def epydoc_func(first: str, second: int = 0) -> int:
    """Do something useful with Epydoc style.

    @param first: the first argument
    @type first: str
    @param second: the second argument
    @type second: int
    @return: the result value
    @rtype: int
    @raise KeyError: when key is not found
    """
    return len(first) + second
