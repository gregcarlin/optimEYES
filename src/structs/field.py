from typing import Generic, TypeVar
from dataclasses import dataclass
from abc import ABC, abstractmethod

from dateutil import Weekday

TVal = TypeVar("TVal")


@dataclass
class Field(Generic[TVal], ABC):
    value: TVal

    """
    @abstractmethod
    def validate(self) -> None:
        pass
    """


@dataclass
class WeekdayField(Field[Weekday]):
    pass


@dataclass
class WeekdayListField(Field[list[Weekday]]):
    pass


@dataclass
class IntField(Field[int]):
    minimum: int | None = None
    maximum: int | None = None


@dataclass
class StringField(Field[str]):
    allowed_values: list[str] | None = None
