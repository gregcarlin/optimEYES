from typing import Mapping, Sequence

from datetime import date, timedelta

from dateutil import Weekday, days_until_next_weekday


class InputBuilder:
    def __init__(
        self, start_date: date, availability: Mapping[str, Sequence[int]]
    ) -> None:
        self.start_date = start_date
        # TODO validate initial availability
        self.availability = {resident: list(a) for resident, a in availability.items()}
        self.num_days = len(next(iter(availability.values())))

    def assign_to_day_of_week(self, resident: str, weekday: Weekday) -> None:
        index = days_until_next_weekday(self.start_date, weekday)
        while index < self.num_days:
            for res, days in self.availability.items():
                if res == resident:
                    assert (
                        days[index] == 1
                    ), f"Trying to assign {resident} to {self.start_date + timedelta(days=index)} (day {index}) but they're marked unavailable."
                days[index] = 1 if res == resident else 0
            index += 7

    def get_availability(self) -> Mapping[str, Sequence[int]]:
        # TODO validate result
        return self.availability
