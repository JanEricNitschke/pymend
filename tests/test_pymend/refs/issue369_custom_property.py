from functools import cached_property


class TestClass:
    @cached_property
    def value(self) -> int:
        """The value."""
        return 1
