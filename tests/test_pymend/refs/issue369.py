"""Test file for issue 369."""


class TestClass:
    """Class with a documented property."""

    def __init__(self, a: int):
        """Initialize the class.

        Parameters
        ----------
        a : int
            The value of a.
        """
        self._a = a

    @property
    def a(self) -> int:
        """The value of a."""
        return self._a

    @a.setter
    def a(self, value: int) -> None:
        """Set the value of a.

        Parameters
        ----------
        value : int
            The new value of a.
        """
        self._a = value

    def get_a(self) -> int:
        """Get the value of a."""
        return self._a
