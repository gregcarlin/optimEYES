from typing import Mapping, Sequence, AbstractSet, List

import itertools

from datetime import date, timedelta
from enum import Enum

from dateutil import Weekday, days_until_next_weekday
from call_problem import Resident


class Availability(Enum):
    UNAVAILABLE = 0
    AVAILABLE = 1
    PREFERRED = 2


class ResidentBuilder:
    def __init__(self, name: str, pgy: int, num_days: int) -> None:
        self.name = name
        self.pgy = pgy
        self.availability = [Availability.AVAILABLE] * num_days
        # Tracks days a resident should be working due to their regular
        # schedule, but will instead get coverage because they're unavailable,
        # eg. due to vacation
        # Map of day -> reason
        self.coverage: dict[int, str] = {}


class AvailabilityBuilder:
    def __init__(
        self, start_date: date, residents: dict[str, int], num_days: int
    ) -> None:
        self.start_date = start_date
        self.num_days = num_days
        self.residents = [
            ResidentBuilder(name, pgy, num_days) for name, pgy in residents.items()
        ]
        errors = self._validate()
        assert errors == [], errors

    def _get_day(self, index: int) -> str:
        day = self.start_date + timedelta(days=index)
        return day.strftime("%a %Y-%m-%d")

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
                if resident.availability[i] != Availability.UNAVAILABLE:
                    break
            else:
                errors.append(
                    f"No residents are available on {self._get_day(i)} (day {i})"
                )
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
            if index < 0:
                continue
            chosen_resident = self._get_resident(next(resident_iter))
            assert (
                chosen_resident.availability[index] != Availability.UNAVAILABLE
            ), f"Trying to assign {chosen_resident} to {self._get_day(index)} (day {index}) but they're marked unavailable."
            chosen_resident.availability[index] = Availability.PREFERRED

    def assign_to_day(self, resident: str, day: str) -> None:
        """
        Assigns the given resident to be on call on the given day.
        """
        index = self._get_index(date.fromisoformat(day))
        chosen_resident = self._get_resident(resident)
        for res in self.residents:
            if res.name == resident:
                assert (
                    res.availability[index] != Availability.UNAVAILABLE
                ), f"Trying to assign {resident} to {self._get_day(index)} (day {index}) but they're marked unavailable."
            else:
                res.availability[index] = Availability.UNAVAILABLE

    def open_for_coverage(self, day: str, reason: str) -> None:
        """
        Marks all residents as available for the given day.
        """
        index = self._get_index(date.fromisoformat(day))
        previous_resident = None
        for res in self.residents:
            if res.availability[index] == Availability.PREFERRED:
                assert previous_resident is None
                previous_resident = res
            res.availability[index] = Availability.AVAILABLE
        assert previous_resident is not None
        previous_resident.coverage[index] = reason

    def _get_resident(self, name: str) -> ResidentBuilder:
        for res in self.residents:
            if res.name == name:
                return res
        raise ValueError(f"Unable to find resident {name}")

    def _set_unavailable_impl(
        self, resident: ResidentBuilder, index: int, reason: str
    ) -> None:
        if resident.availability[index] == Availability.PREFERRED:
            assert index not in resident.coverage
            resident.coverage[index] = reason
        resident.availability[index] = Availability.UNAVAILABLE

    def set_unavailable(
        self, resident_name: str, reason: str, start: str, end: str | None = None
    ) -> None:
        """
        Assigns the resident to be unavailable between the given dates, inclusive.
        """
        resident = self._get_resident(resident_name)
        start_index = max(self._get_index(date.fromisoformat(start)), 0)

        if not end:
            self._set_unavailable_impl(resident, start_index, reason)
            return

        end_index = min(self._get_index(date.fromisoformat(end)) + 1, self.num_days)
        assert end_index > start_index, f"Vacation end {end} is before start {start}"

        for index in range(start_index, end_index):
            self._set_unavailable_impl(resident, index, reason)

    def set_vacation(
        self, resident_name: str, start: str, end: str | None = None
    ) -> None:
        self.set_unavailable(resident_name, "vacation", start, end)

    def set_conference(
        self, resident_name: str, start: str, end: str | None = None
    ) -> None:
        self.set_unavailable(resident_name, "conference", start, end)

    def set_holiday(
        self, resident_name: str, start: str, end: str | None = None
    ) -> None:
        self.set_unavailable(resident_name, "floating holiday", start, end)

    def set_weekend(
        self, resident_name: str, start: str, end: str | None = None
    ) -> None:
        self.set_unavailable(resident_name, "requested weekend", start, end)

    def set_consults(
        self, resident_name: str, start: str, end: str | None = None
    ) -> None:
        self.set_unavailable(resident_name, "consults", start, end)

    def _eliminate_non_preferred(self) -> None:
        for index in range(self.num_days):
            preferred = [
                r.name
                for r in self.residents
                if r.availability[index] == Availability.PREFERRED
            ]
            assert (
                len(preferred) <= 1
            ), f"Multiple residents are preferred for {self._get_day(index)}: {preferred}"
            if preferred != []:
                # Someone is preferred, mark everyone else unavailable
                for r in self.residents:
                    if r.availability[index] != Availability.PREFERRED:
                        r.availability[index] = Availability.UNAVAILABLE

    def _convert_availability(self, availability: list[Availability]) -> list[int]:
        return [0 if x == Availability.UNAVAILABLE else 1 for x in availability]

    def build(self) -> AbstractSet[Resident] | list[str]:
        self._eliminate_non_preferred()

        errors = self._validate()
        if errors != []:
            return errors

        return {
            Resident(
                r.name, r.pgy, self._convert_availability(r.availability), r.coverage
            )
            for r in self.residents
        }
