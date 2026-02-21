from typing import Generic, TypeVar, override, Self
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
class OptionField(Generic[TVal], Field[TVal]):
    allowed_values: list[TVal]

    def parse(self, index: int) -> Self:
        return self.__class__(
            self.allowed_values[index],
            self.name,
            self.allowed_values,
        )

    @abstractmethod
    def allowed_value_labels(self) -> list[str]:
        pass


@dataclass
class WeekdayField(OptionField[Weekday]):
    def __init__(self, value: Weekday, name: str) -> None:
        super().__init__(value, name, [w for w in Weekday])

    @override
    def parse(self, index: int) -> "WeekdayField":
        return WeekdayField(self.allowed_values[index], self.name)

    @override
    def allowed_value_labels(self) -> list[str]:
        return [w.human_name() for w in self.allowed_values]


@dataclass
class WeekdayListField(Field[set[Weekday]]):
    def parse(self, checks: list[bool]) -> "WeekdayListField":
        assert len(checks) == len(Weekday)
        checked = {day for check, day in zip(checks, Weekday) if check}
        return WeekdayListField(checked, self.name)


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
        if self.minimum is not None and i_val < self.minimum:
            return IntermediateSentinel.VAL
        if self.maximum is not None and i_val > self.maximum:
            return IntermediateSentinel.VAL
        return IntField(i_val, self.name, self.minimum, self.maximum)


@dataclass
class StringField(TextInputField[str]):
    @override
    def parse(self, val: str) -> "StringField | IntermediateSentinel | None":
        if val == "":
            return IntermediateSentinel.VAL
        return StringField(val, self.name)


@dataclass
class LimitedStringField(OptionField[str]):
    @override
    def allowed_value_labels(self) -> list[str]:
        return self.allowed_values


@dataclass
class FileField(Field[str]):
    pass
