from typing import Mapping, Sequence, AbstractSet, List

from datetime import date, timedelta

from dateutil import Weekday, days_until_next_weekday
from call_problem import Resident


class InputBuilder:
    def __init__(self, start_date: date, residents: AbstractSet[Resident]) -> None:
        self.start_date = start_date
        self.num_days = len(next(iter(residents)).availability)
        self.residents = residents
        self._validate()

    def _get_day(self, index: int) -> date:
        return self.start_date + timedelta(days=index)

    def _get_index(self, day: date) -> int:
        return (day - self.start_date).days

    def _validate(self) -> None:
        self._validate_num_days_are_equal()
        self._validate_no_days_without_availability()
        # TODO maybe add other validations

    def _validate_num_days_are_equal(self) -> None:
        for resident in self.residents:
            assert (
                len(resident.availability) == self.num_days
            ), f"Number of days for {resident.name} is {len(resident.availability)}, expected {self.num_days}"

    def _validate_no_days_without_availability(self) -> None:
        for i in range(self.num_days):
            for resident in self.residents:
                if resident.availability[i] == 1:
                    break
            else:
                assert (
                    False
                ), f"No residents are available on {self._get_day(i)} (day {i})"

    def assign_to_day_of_week(
        self, resident: str, weekday: Weekday, start: str, end: str
    ) -> None:
        """
        Assigns the given resident to be on call every given weekday between the two dates.
        Both the start and end dates are inclusive.
        """
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)

        start_index = self._get_index(start_date) + days_until_next_weekday(
            start_date, weekday
        )
        end_index = min(self._get_index(end_date) + 1, self.num_days)
        for index in range(start_index, end_index, 7):
            for res in self.residents:
                if res.name == resident:
                    assert (
                        res.availability[index] == 1
                    ), f"Trying to assign {resident} to {self._get_day(index)} (day {index}) but they're marked unavailable."
                res.availability[index] = 1 if res.name == resident else 0

    def build(self) -> AbstractSet[Resident]:
        self._validate()
        return self.residents
