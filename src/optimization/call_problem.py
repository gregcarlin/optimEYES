from typing import Mapping, Sequence
from abc import ABC, abstractmethod
from datetime import date

from optimization.linear_problem import Variable, PulpProblem
from structs.resident import Resident
from dateutil import Weekday


class CallProblemBuilder(ABC):
    @abstractmethod
    def get_num_days(self) -> int:
        pass

    @abstractmethod
    def get_start_date(self) -> date:
        pass

    @abstractmethod
    def get_num_residents(self) -> int:
        pass

    @abstractmethod
    def get_residents(self) -> Mapping[str, Resident]:
        pass

    @abstractmethod
    def get_problem(self) -> PulpProblem:
        pass

    @abstractmethod
    def get_day_vars(self) -> dict[str, list[Variable]]:
        pass

    @abstractmethod
    def get_qn_vars(self, n: int = 2) -> Mapping[str, Sequence[Variable]]:
        pass

    @abstractmethod
    def get_vars_for_weekday(self, resident: str, weekday: Weekday) -> list[Variable]:
        pass

    @abstractmethod
    def get_va_vars(self) -> list[Variable]:
        pass

    @abstractmethod
    def get_min_by_year(self, pgy: int) -> Variable:
        pass

    @abstractmethod
    def get_max_by_year(self, pgy: int) -> Variable:
        pass
