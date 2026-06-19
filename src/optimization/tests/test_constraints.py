import unittest
from typing import cast
from datetime import date, timedelta

from optimization.constraint import (
    DistributeWithinPGYConstraint,
    DistributeDayOfWeekConstraint,
)
from optimization.objective import ChangesFromPreviousSolutionObjective
from optimization.call_problem_impl import CallProblemBuilderImpl
from optimization.solution import Solution
from optimization.availability import AvailabilityConstraint
from structs.project import Project
from structs.resident import Resident


NAMES = ["Barnaby", "Sprocket", "Pippin", "Kevin"]


class ConstraintTest(unittest.TestCase):
    @staticmethod
    def _parse_spec(spec: str, names: list[str] | None = None) -> list[list[str]]:
        result = []
        i = 0
        while i < len(spec):
            if spec[i] == "[":
                close = spec.index("]", i)
                result.append(list(spec[i + 1 : close]))
                i = close + 1
            else:
                result.append([spec[i]])
                i += 1

        if names is not None:
            name_dict = {name[0]: name for name in names}
            result = [[name_dict[day] for day in days] for days in result]

        return result

    def _get_resident(
        self, name: str, pgy: int, availability: list[list[str]]
    ) -> Resident:
        return Resident(
            name,
            pgy,
            [1 if name[0] in d else 0 for d in availability],
            [0] * len(availability),
        )

    def _get_project(self, spec: str) -> Project:
        availability = ConstraintTest._parse_spec(spec)
        start_date = date(2026, 1, 1)
        num_days = len(availability)
        end_date = start_date + timedelta(days=num_days)
        return Project(
            start_date=start_date,
            end_date=end_date,
            buddy_period=None,
            availability=[
                self._get_resident(
                    "Barnaby",
                    2,
                    availability,
                ),
                self._get_resident(
                    "Sprocket",
                    2,
                    availability,
                ),
                self._get_resident(
                    "Pippin",
                    3,
                    availability,
                ),
                self._get_resident(
                    "Kevin",
                    3,
                    availability,
                ),
            ],
            coverage=[""] * num_days,
            seed=12345,
            constraints=[],
            objectives=[],
        )

    def assert_solution(self, solution: Solution | str, result_spec: str) -> None:
        expected_result = ConstraintTest._parse_spec(result_spec)
        self.assertIsInstance(solution, Solution)
        solution = cast(Solution, solution)
        actual_result = [
            [day[0] for day in days] for days in solution.get_assignments()
        ]
        self.assertEqual(expected_result, actual_result)

    def test_distribute_within_pgy(self):
        # Only Barnaby and Kevin available, must pick Kevin otherwise Barnaby
        # will have two more than Sprocket
        project = self._get_project("BP[BK]SB")
        builder = CallProblemBuilderImpl(project)
        builder.apply_constraints(
            [AvailabilityConstraint(), DistributeWithinPGYConstraint()]
        )
        builder.set_objectives(
            [
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BPBSB", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BPKSB")
