import unittest
from datetime import date, timedelta

from optimization.constraint import (
    DistributeWithinPGYConstraint,
    DistributeDayOfWeekConstraint,
)
from optimization.objective import ChangesFromPreviousSolutionObjective
from optimization.call_problem_impl import CallProblemBuilderImpl
from structs.project import Project
from structs.resident import Resident


class ConstraintTest(unittest.TestCase):
    def _get_project(self, spec: str) -> Project:
        availability = spec.split(",")
        start_date = date(2026, 1, 1)
        num_days = len(availability)
        end_date = start_date + timedelta(days=num_days)
        return Project(
            start_date=start_date,
            end_date=end_date,
            buddy_period=None,
            availability=[
                Resident(
                    "Barnaby",
                    2,
                    [1 if "B" in d else 0 for d in availability],
                    [0] * num_days,
                ),
                Resident(
                    "Sprocket",
                    2,
                    [1 if "S" in d else 0 for d in availability],
                    [0] * num_days,
                ),
                Resident(
                    "Pippin",
                    3,
                    [1 if "P" in d else 0 for d in availability],
                    [0] * num_days,
                ),
                Resident(
                    "Kevin",
                    3,
                    [1 if "K" in d else 0 for d in availability],
                    [0] * num_days,
                ),
            ],
            coverage=[""] * num_days,
            seed=12345,
            constraints=[],
            objectives=[],
        )

    def test_distribute_within_pgy(self):
        project = self._get_project("B,S,P")
        builder = CallProblemBuilderImpl(project)
        builder.apply_constraints([DistributeWithinPGYConstraint()])  # TODO
        builder.set_objectives(
            [ChangesFromPreviousSolutionObjective("fake", [])]
        )  # TODO
