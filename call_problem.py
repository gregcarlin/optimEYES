from typing import Mapping, Sequence

import math
from datetime import date, timedelta

from solution import Solution, key_for_day
from dateutil import days_until_next_weekday, num_weekdays_in_time_period
from linear_problem import PulpProblem, new_binary_variable, new_continuous_variable


class CallProblemBuilder:
    def __init__(
        self, start_date: date, resident_availability: Mapping[str, Sequence[int]]
    ) -> None:
        self.start_date = start_date
        self.resident_availability = resident_availability

        self.problem = PulpProblem("optimEYES", minimize=True)

        self.num_days = len(next(iter(resident_availability.values())))
        self.num_residents = len(resident_availability.keys())

        min_days_per_resident = math.floor(self.num_days / float(self.num_residents))
        max_days_per_resident = math.ceil(self.num_days / float(self.num_residents))

        # For each resident, create a variable representing every day
        self.day_vars = {resident: [] for resident in resident_availability.keys()}
        for resident, availability in resident_availability.items():
            for day, is_available in enumerate(availability):
                day_var = new_binary_variable(key_for_day(day, resident))
                self.day_vars[resident].append(day_var)
                if is_available == 0:
                    # Resident is unavailable this day
                    self.problem.add_constraint(day_var == 0)

            # Ensure even distribution
            self.problem.add_constraint(
                sum(self.day_vars[resident]) >= min_days_per_resident
            )
            self.problem.add_constraint(
                sum(self.day_vars[resident]) <= max_days_per_resident
            )

        # Ensure exactly one resident is assigned to each day
        for day in range(self.num_days):
            all_residents_for_day = [
                days_for_resident[day] for days_for_resident in self.day_vars.values()
            ]
            self.problem.add_constraint(sum(all_residents_for_day) == 1)

        # Ensure a resident doesn't work two days in a row
        for days_for_resident in self.day_vars.values():
            for i in range(len(days_for_resident) - 1):
                self.problem.add_constraint(
                    days_for_resident[i] + days_for_resident[i + 1] <= 1
                )

    def evenly_distribute_weekday(self, weekday: int) -> None:
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

    def minimize_q2s(self) -> None:
        q2s = []
        for resident, days_for_resident in self.day_vars.items():
            for i in range(len(days_for_resident) - 2):
                var = new_binary_variable(f"q2_{resident}_{i}")
                var_slack = new_continuous_variable(f"q2_{resident}_{i}_cont", 0, 0.9)
                self.problem.add_constraint(
                    0.5 * days_for_resident[i] + 0.5 * days_for_resident[i + 2]
                    == var + var_slack
                )
                q2s.append(var)
        self.problem.set_objective(sum(q2s))

    def solve(self) -> Solution | str:
        solution = self.problem.solve()
        if not solution.was_successful():
            return solution.get_status()

        return Solution(
            solution.get_objective_value(),
            solution.get_variables(),
            self.start_date,
            self.num_days,
            self.resident_availability.keys(),
        )
