from typing import Mapping, Sequence

from datetime import date, timedelta

from dateutil import Weekday, days_until_next_weekday


class InputBuilder:
    def __init__(
        self, start_date: date, availability: Mapping[str, Sequence[int]]
    ) -> None:
        self.start_date = start_date
        self.num_days = len(next(iter(availability.values())))
        self.availability = {resident: list(a) for resident, a in availability.items()}
        self._validate()

    def _get_day(self, index: int) -> date:
        return self.start_date + timedelta(days=index)

    def _validate(self) -> None:
        self._validate_no_days_without_availability()
        # TODO maybe add other validations

    def _validate_no_days_without_availability(self) -> None:
        for i in range(self.num_days):
            for days in self.availability.values():
                if days[i] == 1:
                    break
            else:
                assert (
                    False
                ), f"No residents are available on {self._get_day(i)} (day {i})"

    # TODO add start and end
    def assign_to_day_of_week(self, resident: str, weekday: Weekday) -> None:
        index = days_until_next_weekday(self.start_date, weekday)
        while index < self.num_days:
            for res, days in self.availability.items():
                if res == resident:
                    assert (
                        days[index] == 1
                    ), f"Trying to assign {resident} to {self._get_day(index)} (day {index}) but they're marked unavailable."
                days[index] = 1 if res == resident else 0
            index += 7

    def get_availability(self) -> Mapping[str, Sequence[int]]:
        self._validate()
        return self.availability
