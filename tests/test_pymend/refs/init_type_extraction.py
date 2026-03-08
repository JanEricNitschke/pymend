"""Reference file for __init__ type extraction."""


class AnnotatedInit:
    """Class with annotated self assignments in __init__."""

    def __init__(self) -> None:
        self.x: int = 5
        self.y: str = "hello"


class ParamMappingInit:
    """Class with self.x = x param mapping in __init__."""

    def __init__(self, x: int, y: str) -> None:
        self.x = x
        self.y = y


class MixedInit:
    """Class with mixed type sources in __init__."""

    def __init__(self, a: int, b) -> None:
        self.a = a
        self.b = b
        self.c: float = 3.14
        self.d = "literal"
