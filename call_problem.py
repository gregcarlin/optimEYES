from typing import Mapping, Sequence, List, AbstractSet

import math
from datetime import date, timedelta
from collections import defaultdict

from solution import Solution, key_for_day
from dateutil import days_until_next_weekday, num_weekdays_in_time_period, Weekday
from linear_problem import (
    PulpProblem,
    Variable,
)


class Resident:
    def __init__(self, name: str, pgy: int, num_days: int) -> None:
        self.name = name
        self.pgy = pgy
        self.availability = [1] * num_days


class CallProblemBuilder:
    def __init__(
        self,
        start_date: date,
        buddy_period: tuple[date, date] | None,
        resident_availability: AbstractSet[Resident],
        debug_infeasibility: bool = False,
    ) -> None:
        self.start_date = start_date
        self.residents = {resident.name: resident for resident in resident_availability}

        self.problem = PulpProblem(
            "optimEYES", minimize=True, debug_infeasibility=debug_infeasibility
        )

        self.num_days = len(next(iter(resident_availability)).availability)
        self.num_residents = len(resident_availability)

        min_days_per_resident = math.floor(self.num_days / float(self.num_residents))
        max_days_per_resident = math.ceil(self.num_days / float(self.num_residents))

        # For each resident, create a variable representing every day
        self.day_vars = {resident.name: [] for resident in resident_availability}
        for resident in resident_availability:
            for day, is_available in enumerate(resident.availability):
                day_var = self.problem.new_binary_variable(
                    key_for_day(day, resident.name)
                )
                self.day_vars[resident.name].append(day_var)
                if is_available == 0:
                    # Resident is unavailable this day
                    self.problem.add_constraint(day_var == 0)

            # Ensure even distribution
            self.problem.add_constraint(
                sum(self.day_vars[resident.name]) >= min_days_per_resident
            )
            self.problem.add_constraint(
                sum(self.day_vars[resident.name]) <= max_days_per_resident
            )

        if buddy_period:
            buddy_start, buddy_end = buddy_period

            buddy_start_index = (buddy_start - self.start_date).days
            buddy_end_index = (buddy_end - self.start_date).days  # inclusive
            assert (
                buddy_start_index >= 0 and buddy_start_index < self.num_days
            ), "Invalid buddy call start date"
            assert (
                buddy_end_index >= 0 and buddy_end_index < self.num_days
            ), "Invalid buddy call end date"

            self._ensure_one_resident_per_day(range(buddy_start_index))
            for day in range(buddy_start_index, buddy_end_index + 1):
                # Ensure one PGY2 and either one PGY3 or PGY4 is assigned to each day
                vars_by_pgy = self._vars_for_day_by_pgy(day)
                self.problem.add_constraint(sum(vars_by_pgy[2]) == 1)
                self.problem.add_constraint(sum(vars_by_pgy[3] + vars_by_pgy[4]) == 1)
                remaining_vars = [
                    v
                    for pgy, vs in vars_by_pgy.items()
                    if pgy != 2 and pgy != 3
                    for v in vs
                ]
                if remaining_vars != []:
                    self.problem.add_constraint(sum(remaining_vars) == 0)
            self._ensure_one_resident_per_day(range(buddy_end_index + 1, self.num_days))
        else:
            self._ensure_one_resident_per_day(range(self.num_days))

        # Ensure a resident doesn't work two days in a row
        for days_for_resident in self.day_vars.values():
            for i in range(len(days_for_resident) - 1):
                self.problem.add_constraint(
                    days_for_resident[i] + days_for_resident[i + 1] <= 1
                )

        self.q2s: Mapping[str, List[Variable]] | None = None

    def _ensure_one_resident_per_day(self, indices: range) -> None:
        # Ensure exactly one resident is assigned to each day in the given range
        for day in indices:
            all_residents_for_day = [
                days_for_resident[day] for days_for_resident in self.day_vars.values()
            ]
            self.problem.add_constraint(sum(all_residents_for_day) == 1)

    def _vars_for_day_by_pgy(self, day: int) -> Mapping[int, List[Variable]]:
        result = defaultdict(list)
        for name, days_for_resident in self.day_vars.items():
            result[self.residents[name].pgy].append(days_for_resident[day])
        return result

    def evenly_distribute_weekday(self, weekday: Weekday) -> None:
        num_weekdays = num_weekdays_in_time_period(
            self.start_date, self.num_days, weekday
        )
        min_weekdays_per_resident = math.floor(num_weekdays / float(self.num_residents))
        max_weekdays_per_resident = math.ceil(num_weekdays / float(self.num_residents))
        for days_for_resident in self.day_vars.values():
            day_of_week_vars = []
            next_day = days_until_next_weekday(self.start_date, weekday)
            while next_day < self.num_days:
                day_of_week_vars.append(days_for_resident[next_day])
                next_day += 7
            self.problem.add_constraint(
                sum(day_of_week_vars) >= min_weekdays_per_resident
            )
            self.problem.add_constraint(
                sum(day_of_week_vars) <= max_weekdays_per_resident
            )

    def _get_q2_vars(self) -> Mapping[str, Sequence[Variable]]:
        if self.q2s is not None:
            return self.q2s
        self.q2s = {}
        for resident, days_for_resident in self.day_vars.items():
            self.q2s[resident] = []
            for i in range(len(days_for_resident) - 2):
                var = self.problem.new_binary_variable(f"q2_{resident}_{i}")
                var_slack = self.problem.new_continuous_variable(
                    f"q2_{resident}_{i}_cont", 0, 0.9
                )
                self.problem.add_constraint(
                    0.5 * days_for_resident[i] + 0.5 * days_for_resident[i + 2]
                    == var + var_slack
                )
                self.q2s[resident].append(var)
        return self.q2s

    def minimize_q2s(self) -> None:
        q2s_dict = self._get_q2_vars()
        q2s = [v for vs in q2s_dict.values() for v in vs]
        self.problem.set_objective(sum(q2s))

    def evenly_distribute_q2s(self, tolerance: int = 0) -> None:
        q2s_dict = self._get_q2_vars()
        q2s_per_resident = [sum(q2_vars) for q2_vars in q2s_dict.values()]
        max_q2s = self.problem.max_of(q2s_per_resident, self.num_days, "max_q2s")
        min_q2s = self.problem.min_of(q2s_per_resident, self.num_days, "min_q2s")
        self.problem.add_constraint(max_q2s - min_q2s <= tolerance)

    def solve(self) -> Solution | str:
        solution = self.problem.solve()
        if not solution.was_successful():
            return solution.get_status()

        return Solution(
            solution.get_objective_value(),
            solution.get_variables(),
            self.start_date,
            self.num_days,
            self.residents.keys(),
        )
