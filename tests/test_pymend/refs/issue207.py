"""Reference file for issue 207."""


def multi_return_with_sig(version: str) -> tuple[int, str]:
    """Do something.

    Args:
        version (str): The version.

    Returns:
        int: An integer value.
        str: A string value.
    """
    return 1, "hello"


def multi_return_no_sig(version):
    """Do something.

    Args:
        version: The version.

    Returns:
        int: An integer value.
        str: A string value.
    """
    return 1, "hello"
