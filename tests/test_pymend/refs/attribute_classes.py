"""Reference file for attribute class extraction."""

from dataclasses import dataclass


@dataclass
class SimpleDataclass:
    x: int
    y: str = "hello"


@dataclass(frozen=True)
class FrozenDataclass:
    name: str
    value: float


class SimpleModel(BaseModel):
    x: int
    y: str = "hello"


class DottedModel(pydantic.BaseModel):
    name: str
    value: float


class PlainClass:
    x: int
    y: str = "hello"
