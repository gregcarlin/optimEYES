from typing import Generic, TypeVar, override, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import IntEnum

from dateutil import Weekday

TVal = TypeVar("TVal")


class IntermediateSentinel(IntEnum):
    VAL = 0


@dataclass
class Field(Generic[TVal], ABC):
    value: TVal
    name: str


@dataclass
class TextInputField(Generic[TVal], Field[TVal]):
    @abstractmethod
    def parse(self, val: str) -> "TextInputField | IntermediateSentinel | None":
        pass


@dataclass
class WeekdayField(Field[Weekday]):
    pass


@dataclass
class WeekdayListField(Field[list[Weekday]]):
    pass


@dataclass
class IntField(TextInputField[int]):
    minimum: int | None = None
    maximum: int | None = None

    @override
    def parse(self, val: str) -> "IntField | IntermediateSentinel | None":
        if val == "":
            return IntermediateSentinel.VAL
        try:
            i_val = int(val)
        except ValueError:
            return None
        if not (self.minimum is None or i_val >= self.minimum) and (
            self.maximum is None or i_val <= self.maximum
        ):
            return IntermediateSentinel.VAL
        return IntField(i_val, self.name, self.minimum, self.maximum)


@dataclass
class StringField(TextInputField[str]):
    allowed_values: list[str] | None = None

    @override
    def parse(self, val: str) -> "StringField | IntermediateSentinel | None":
        if self.allowed_values is not None and self.value not in self.allowed_values:
            return IntermediateSentinel.VAL
        return StringField(val, self.name, self.allowed_values)
