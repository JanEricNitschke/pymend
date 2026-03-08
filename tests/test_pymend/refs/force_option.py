"""Reference file for ForceOption tests."""


def fully_typed(x: int, y: str) -> bool:
    """All types present in signature and docstring.

    Parameters
    ----------
    x : int
        First param.
    y : str
        Second param.

    Returns
    -------
    bool
        The result.
    """
    return x > 0


def no_sig_types(x, y):
    """No signature types, docstring has placeholders.

    Parameters
    ----------
    x : _type_
        First param.
    y : _type_
        Second param.
    """
    pass


def mixed_sig_types(x: int, y) -> float:
    """Some signature types, some not. Doc types differ from sig where present.

    Parameters
    ----------
    x : wrong
        First param.
    y : also_wrong
        Second param.

    Returns
    -------
    float
        The result.
    """
    return 1.0


def doc_types_no_sig(x, y):
    """No signature types but docstring has real types.

    Parameters
    ----------
    x : int
        First param.
    y : str
        Second param.
    """
    pass


def typed_sig_no_doc_type(x: int, y: str) -> float:
    """Typed signature but docstring entries have no types.

    Parameters
    ----------
    x
        First param.
    y
        Second param.

    Returns
    -------
    float
        The result.
    """
    return 1.0


def wrong_return_type(x: int) -> int:
    """Return type in docstring differs from signature.

    Parameters
    ----------
    x : int
        Input value.

    Returns
    -------
    str
        The result.
    """
    return x


def no_docstring_typed(x: int) -> str:
    return "hello"


def no_docstring_untyped(x):
    return x


def named_return_typed(x: int) -> bool:
    """Function with named return type.

    Parameters
    ----------
    x : int
        Input value.

    Returns
    -------
    result : bool
        The result.
    """
    return x > 0
