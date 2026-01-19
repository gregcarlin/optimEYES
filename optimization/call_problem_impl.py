from typing import Mapping, Sequence, List, AbstractSet, override

import math
from datetime import date, timedelta
from collections import defaultdict

from optimization.call_problem import CallProblemBuilder
from optimization.solution import Solution, key_for_day
from optimization.constraint import Constraint, SerializableConstraint
from optimization.objective import combine_objectives, Objective, SerializableObjective
from project import Project
from dateutil import days_until_next_weekday, num_weekdays_in_time_period, Weekday
from structs.resident import Resident
from optimization.linear_problem import (
    PulpProblem,
    Variable,
    VariableLike,
)


class CallProblemBuilderImpl(CallProblemBuilder):
    def __init__(
        self,
        project: Project,
        resident_availability: AbstractSet[Resident],
        debug_infeasibility: bool = False,
    ) -> None:
        self.start_date = project.start_date
        self.residents = {resident.name: resident for resident in resident_availability}

        self.problem = PulpProblem(
            "optimEYES",
            minimize=True,
            debug_infeasibility=debug_infeasibility,
            seed=project.seed,
        )

        self.num_days = len(next(iter(resident_availability)).availability)
        self.num_residents = len(resident_availability)
        self.soft_unavailable_days: list[Variable] = []

        # For each resident, create a variable representing every day
        self.day_vars = {resident.name: [] for resident in resident_availability}
        for resident in resident_availability:
            for day in range(len(resident.availability)):
                day_var = self.problem.new_binary_variable(
                    key_for_day(day, resident.name)
                )
                self.day_vars[resident.name].append(day_var)

        # Ensure even distribution within a year
        calls_per_resident_by_year = defaultdict(list)
        for resident in resident_availability:
            calls_per_resident_by_year[resident.pgy].append(
                self.day_vars[resident.name]
            )
        mins = {}
        maxs = {}
        for year, calls_per_resident in calls_per_resident_by_year.items():
            upper = self.problem.max_of(
                calls_per_resident, self.num_days, f"max_calls_pgy{year}"
            )
            lower = self.problem.min_of(
                calls_per_resident, self.num_days, f"min_calls_pgy{year}"
            )
            self.problem.add_constraint(upper - lower <= 1)
            maxs[year] = upper
            mins[year] = lower
        # Ensure pgy2s and 3s aren't too far apart
        assert 2 in calls_per_resident_by_year, "PGY2 year not found"
        assert 3 in calls_per_resident_by_year, "PGY3 year not found"
        self.problem.add_constraint(maxs[2] - mins[3] <= project.pgy_2_3_gap)

        if project.buddy_period:
            buddy_start, buddy_end = project.buddy_period

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

        # Cache of q2s, q3s, etc
        self.qns: dict[int, dict[str, List[Variable]]] = {}
        self.va_vars: list[Variable] | None = None

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

    @override
    def get_num_days(self) -> int:
        return self.num_days

    @override
    def get_start_date(self) -> date:
        return self.start_date

    @override
    def get_num_residents(self) -> int:
        return self.num_residents

    @override
    def get_residents(self) -> Mapping[str, Resident]:
        return self.residents

    @override
    def get_problem(self) -> PulpProblem:
        return self.problem

    @override
    def get_day_vars(self) -> dict[str, list[Variable]]:
        return self.day_vars

    @override
    def get_vars_for_weekday(self, resident: str, weekday: Weekday) -> list[Variable]:
        day = days_until_next_weekday(self.start_date, weekday)
        day_vars = []
        while day < self.num_days:
            day_vars.append(self.day_vars[resident][day])
            day += 7
        return day_vars

    @override
    def get_va_vars(self) -> list[Variable]:
        if self.va_vars is not None:
            return self.va_vars
        self.va_vars = []
        for name, days_for_resident in self.day_vars.items():
            for i, v in enumerate(days_for_resident):
                if self.residents[name].va[i]:
                    self.va_vars.append(v)
        return self.va_vars

    @override
    def get_qn_vars(self, n: int = 2) -> Mapping[str, Sequence[Variable]]:
        assert n >= 2, f"Invalid value for n: {n}"
        if n in self.qns:
            return self.qns[n]

        result = {}
        for resident, days_for_resident in self.day_vars.items():
            result[resident] = []
            for i in range(len(days_for_resident) - n):
                var = self.problem.new_binary_variable(f"q{n}_{resident}_{i}")
                var_slack = self.problem.new_continuous_variable(
                    f"q{n}_{resident}_{i}_cont", 0, 0.9
                )
                self.problem.add_constraint(
                    0.5 * days_for_resident[i] + 0.5 * days_for_resident[i + n]
                    == var + var_slack
                )
                result[resident].append(var)
        self.qns[n] = result
        return result

    def apply_constraints(
        self, constraints: list[Constraint] | list[SerializableConstraint]
    ) -> None:
        for constraint_builder in constraints:
            for constraint in constraint_builder.get_constraints(self):
                self.problem.add_constraint(constraint)

    def set_objectives(
        self, objective_hierarchy: list[Objective] | list[SerializableObjective]
    ) -> None:
        objective = combine_objectives(self, objective_hierarchy)
        self.problem.set_objective(objective)

    def solve(self) -> Solution | str:
        solution = self.problem.solve()
        if not solution.was_successful():
            return solution.get_status()

        return Solution(
            solution.get_objective_value(),
            solution.get_variables(),
            self.start_date,
            self.num_days,
            self.residents,
            {},  # TODO
        )
