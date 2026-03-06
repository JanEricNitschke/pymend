"""_summary_."""


def generator() -> Tuple[int, int, str]:
    """_summary_.

    Returns
    -------
    a : int
        Something
    b : int
        Something else

    Yields
    ------
    x : int
        _description_
    z : str
        desc.
    """
    if False:
        return a, b, c
    yield x, y, z


def generator() -> str:
    """_summary_.

    Returns
    -------
    _type_
        desc
    """
    if False:
        return a
    yield b


def generator() -> str:
    """_summary_.

    Returns
    -------
    _type_
        desc
    """
    return a


def generator() -> Iterable[str]:
    """_summary_."""
    yield "test"


def generator() -> Iterator[str]:
    """_summary_.

    Yields
    ------
    Nope
        _description_
    """
    pass


def generator() -> Generator[int, float, str]:
    """_summary_."""
    if False:
        return a
    yield b


# Y1: Generator annotation, both Returns + Yields sections exist.
#     Return type updated to str (3rd arg), yield type updated to int (1st arg).
def generator_gen_both_sections() -> Generator[int, float, str]:
    """_summary_.

    Returns
    -------
    _type_
        desc

    Yields
    ------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y2: Generator annotation, Returns section only.
#     Return type updated to str. Yields section added with type int.
def generator_gen_returns_only() -> Generator[int, float, str]:
    """_summary_.

    Returns
    -------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y3: Generator annotation, Yields section only.
#     Yields type updated to int. Returns section added with type str.
def generator_gen_yields_only() -> Generator[int, float, str]:
    """_summary_.

    Yields
    ------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y4 is already covered by the existing Generator[int, float, str] test above.


# Y5: Plain annotation, both Returns + Yields sections exist.
#     yields_value blocks return type correction. sig_yield=None. No changes.
def generator_plain_both_sections() -> str:
    """_summary_.

    Returns
    -------
    _type_
        desc

    Yields
    ------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y6 is already covered by the existing `generator() -> str` with Returns only.


# Y7: Plain annotation, Yields section only.
#     Returns section added (type str). Yield type unchanged (sig_yield=None).
def generator_plain_yields_only() -> str:
    """_summary_.

    Yields
    ------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y8: Plain annotation, neither section.
#     Returns added (type str). Yields added (type _type_).
def generator_plain_none() -> str:
    """_summary_."""
    if False:
        return a
    yield b


# Y9: No annotation, both sections exist. No type info. No changes.
def generator_none_both_sections():
    """_summary_.

    Returns
    -------
    _type_
        desc

    Yields
    ------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y10: No annotation, Returns section only. Yields added.
def generator_none_returns_only():
    """_summary_.

    Returns
    -------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y11: No annotation, Yields section only. Returns added.
def generator_none_yields_only():
    """_summary_.

    Yields
    ------
    _type_
        desc
    """
    if False:
        return a
    yield b


# Y12: No annotation, neither section. Both added.
def generator_none_none():
    """_summary_."""
    if False:
        return a
    yield b
