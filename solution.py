from typing import Dict, List
from datetime import date

from dateutil import days_until_next_weekday

def key_for_day(day: int, resident: str) -> str:
    return f"Day_{day}_{resident}"

class Solution:
    def __init__(self, values: Dict[str, float], start_date: date, num_days: int, residents: List[str]) -> None:
        self.values = values
        self.start_date = start_date
        self.num_days = num_days
        self.residents = residents
        self.assignments = None

    def __getitem__(self, key: str) -> float:
        return self.values[key]

    def get_assignments(self) -> List[str]:
        if self.assignments is not None:
            return self.assignments

        self.assignments = []

        for day in range(self.num_days):
            assigned_resident = None
            for resident in self.residents:
                if self.values[key_for_day(day, resident)] != 0.0:
                    assert assigned_resident is None, "Two residents assigned to the same day"
                    assigned_resident = resident
            assert assigned_resident is not None, "No residents assigned to a day"
            self.assignments.append(assigned_resident)

        return self.assignments

    def get_calls_per_resident(self) -> Dict[str, int]:
        assignments = self.get_assignments()
        return {resident: assignments.count(resident) for resident in self.residents}

    def get_q2s_per_resident(self) -> Dict[str, int]:
        assignments = self.get_assignments()
        result = {resident: 0 for resident in self.residents}
        for day in range(self.num_days - 2):
            if assignments[day] == assignments[day + 2]:
                result[assignments[day]] += 1
        return result

    def _get_count_of_weekday(self, weekday) -> Dict[str, int]:
        assignments = self.get_assignments()
        result = {resident: 0 for resident in self.residents}
        next_day = days_until_next_weekday(self.start_date, weekday)
        while next_day < self.num_days:
            result[assignments[next_day]] += 1
            next_day += 7
        return result

    def get_saturdays(self) -> Dict[str, int]:
        return self._get_count_of_weekday(5)

    def get_sundays(self) -> Dict[str, int]:
        return self._get_count_of_weekday(6)
