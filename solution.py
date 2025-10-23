from typing import Dict, Sequence, Mapping
from datetime import date, timedelta
from collections import defaultdict

from dateutil import days_until_next_weekday
from resident import Resident


def key_for_day(day: int, resident: str) -> str:
    return f"Day_{day}_{resident}"


class Solution:
    def __init__(
        self,
        objective_value: float,
        values: Mapping[str, float],
        start_date: date,
        num_days: int,
        residents: dict[str, Resident],
    ) -> None:
        self.objective_value = objective_value
        self.values = values
        self.start_date = start_date
        self.num_days = num_days
        self.residents = residents
        self.assignments = None

    def __getitem__(self, key: str) -> float:
        return self.values[key]

    def get_objective_value(self) -> float:
        return self.objective_value

    def get_assignments(self) -> Sequence[Sequence[str]]:
        if self.assignments is not None:
            return self.assignments

        self.assignments = []

        for day in range(self.num_days):
            assigned_residents = [
                resident
                for resident in self.residents.keys()
                if self.values[key_for_day(day, resident)] != 0.0
            ]
            assert assigned_residents != [], "No residents assigned to a day"
            self.assignments.append(assigned_residents)

        return self.assignments

    def get_calls_per_resident(self) -> Dict[str, int]:
        result = {resident: 0 for resident in self.residents.keys()}
        for assignments in self.get_assignments():
            for resident in assignments:
                result[resident] += 1
        return result

    def get_q2s_per_resident(self) -> Dict[str, int]:
        assignments = self.get_assignments()
        result = {resident: 0 for resident in self.residents.keys()}
        for day in range(self.num_days - 2):
            for resident in set(assignments[day]).intersection(
                set(assignments[day + 2])
            ):
                result[resident] += 1
        return result

    def get_q2_unfairness(self) -> int:
        """
        Calculate the difference between the maximum number of q2s and the minimum.
        """
        q2s = self.get_q2s_per_resident().values()
        return max(q2s) - min(q2s)

    def get_calls_taken_by_year(self) -> Dict[int, int]:
        result = defaultdict(lambda: 0)
        for assignments in self.get_assignments():
            for resident in assignments:
                result[self.residents[resident].pgy] += 1
        return result

    def _get_count_of_weekday(self, weekday) -> Dict[str, int]:
        assignments = self.get_assignments()
        result = {resident: 0 for resident in self.residents.keys()}
        next_day = days_until_next_weekday(self.start_date, weekday)
        while next_day < self.num_days:
            for resident in assignments[next_day]:
                result[resident] += 1
            next_day += 7
        return result

    def get_saturdays(self) -> Dict[str, int]:
        return self._get_count_of_weekday(5)

    def get_sundays(self) -> Dict[str, int]:
        return self._get_count_of_weekday(6)

    def print(self) -> None:
        for day, residents in enumerate(self.get_assignments()):
            date = self.start_date + timedelta(days=day)
            print(f"\t{date:%a %m-%d}: {', '.join(residents)}")

        print("Total Q2 calls = ", self.get_objective_value())
        print("Q2 unfairness = ", self.get_q2_unfairness())
        calls_by_year = self.get_calls_taken_by_year()
        print(
            f"Calls taken by PGY2s =  {calls_by_year[2]}  ({calls_by_year[2] / self.num_days * 100:.2f}%)"
        )
        print(
            f"Calls taken by PGY3s =  {calls_by_year[3]}  ({calls_by_year[3] / self.num_days * 100:.2f}%)"
        )

        print("Per resident stats:")
        calls = self.get_calls_per_resident()
        saturdays = self.get_saturdays()
        sundays = self.get_sundays()
        q2s = self.get_q2s_per_resident()
        for resident in self.residents.keys():
            print(f"\t{resident}")
            print(f"\t\tCalls = {calls[resident]}")
            print(f"\t\tSaturdays = {saturdays[resident]}")
            print(f"\t\tSundays = {sundays[resident]}")
            print(f"\t\tQ2s = {q2s[resident]}")
