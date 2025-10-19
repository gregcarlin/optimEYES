from typing import Mapping, Sequence, AbstractSet, List

import itertools

from datetime import date, timedelta

from dateutil import Weekday, days_until_next_weekday
from call_problem import Resident


class AvailabilityBuilder:
    def __init__(self, start_date: date, residents: AbstractSet[Resident]) -> None:
        self.start_date = start_date
        self.num_days = len(next(iter(residents)).availability)
        self.residents = residents
        self._validate()

    def _get_day(self, index: int) -> date:
        return self.start_date + timedelta(days=index)

    def _get_index(self, day: date) -> int:
        return (day - self.start_date).days

    def _validate(self) -> list[str]:
        errors = []
        errors += self._validate_num_days_are_equal()
        errors += self._validate_no_days_without_availability()
        # TODO maybe add other validations
        return errors

    def _validate_num_days_are_equal(self) -> list[str]:
        errors = []
        for resident in self.residents:
            if len(resident.availability) != self.num_days:
                errors.append(
                    f"Number of days for {resident.name} is {len(resident.availability)}, expected {self.num_days}"
                )
        return errors

    def _validate_no_days_without_availability(self) -> list[str]:
        errors = []
        for i in range(self.num_days):
            for resident in self.residents:
                if resident.availability[i] == 1:
                    break
            else:
                day = self._get_day(i).strftime("%a %Y-%m-%d")
                errors.append(f"No residents are available on {day} (day {i})")
        return errors

    def assign_to_day_of_week(
        self, residents: str | list[str], weekday: Weekday, start: str, end: str
    ) -> None:
        """
        Assigns the given resident to be on call every given weekday between the two dates.
        If multiple residents are given, does round robin assignment.
        Both the start and end dates are inclusive.
        """
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)

        if isinstance(residents, str):
            residents = [residents]
        resident_iter = itertools.cycle(residents)

        start_index = self._get_index(start_date) + days_until_next_weekday(
            start_date, weekday
        )
        end_index = min(self._get_index(end_date) + 1, self.num_days)
        for index in range(start_index, end_index, 7):
            chosen_resident = next(resident_iter)
            for res in self.residents:
                if res.name == chosen_resident:
                    assert (
                        res.availability[index] == 1
                    ), f"Trying to assign {chosen_resident} to {self._get_day(index)} (day {index}) but they're marked unavailable."
                res.availability[index] = 1 if res.name == chosen_resident else 0

    def _get_resident(self, name: str) -> Resident:
        for res in self.residents:
            if res.name == name:
                return res
        raise ValueError(f"Unable to find resident {name}")

    def set_unavailable(
        self, resident_name: str, start: str, end: str | None = None
    ) -> None:
        """
        Assigns the resident to be unavailable between the given dates, inclusive.
        """
        resident = self._get_resident(resident_name)
        start_index = max(self._get_index(date.fromisoformat(start)), 0)

        if not end:
            resident.availability[start_index] = 0
            return

        end_index = min(self._get_index(date.fromisoformat(end)) + 1, self.num_days)
        assert end_index > start_index, f"Vacation end {end} is before start {start}"

        for index in range(start_index, end_index):
            resident.availability[index] = 0

    def build(self) -> AbstractSet[Resident] | list[str]:
        errors = self._validate()
        if errors != []:
            return errors
        return self.residents
