"""Reference file for existing attribute type correction."""

from dataclasses import dataclass


@dataclass
class WrongTypes:
    """Class where docstring types differ from body types.

    Attributes
    ----------
    x : wrong
        The x value.
    y : also_wrong
        The y value.
    """

    x: int
    y: str


@dataclass
class MissingTypes:
    """Class where docstring attributes lack types.

    Attributes
    ----------
    x
        The x value.
    y
        The y value.
    """

    x: int
    y: str


@dataclass
class MissingFromDocstring:
    """Docstring only lists x but body also has y.

    Attributes
    ----------
    x : int
        The x value.
    """

    x: int
    y: str
