class TestClass:
    def __init__(self, a: int):
        self._a = a

    @property
    def a(self) -> int:
        """The value of a."""
        return self._a
