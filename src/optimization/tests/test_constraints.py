import unittest
from typing import cast
from datetime import date, timedelta

from optimization.constraint import (
    DistributeWithinPGYConstraint,
    DistributeDayOfWeekConstraint,
    DistributeWeekendsConstraint,
    ConstrainWeekdayConstraint,
    LimitWeekdayForResidentConstraint,
    SetMinimumForDaysOfWeekForResidentConstraint,
    NoAdjacentWeekendsConstraint,
)
from optimization.objective import ChangesFromPreviousSolutionObjective
from optimization.call_problem_impl import CallProblemBuilderImpl
from optimization.solution import Solution
from optimization.availability import AvailabilityConstraint
from structs.project import Project
from structs.resident import Resident
from dateutil import Weekday


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

    def _get_builder(self, spec: str) -> CallProblemBuilderImpl:
        availability = ConstraintTest._parse_spec(spec)
        start_date = date(2026, 1, 1)
        num_days = len(availability)
        end_date = start_date + timedelta(days=num_days)
        project = Project(
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

        builder = CallProblemBuilderImpl(project)
        builder.apply_constraints([AvailabilityConstraint()])
        return builder

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
        builder = self._get_builder("BP[BK]SB")
        builder.apply_constraints([DistributeWithinPGYConstraint()])
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BPBSB", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BPKSB")

    def test_distribute_dow(self):
        # Second Thursday can be Barnaby or Sprocket, both PGY2.
        # Barnaby already has one Thursday, so it should be Sprocket
        builder = self._get_builder("BSPKBSP[BS]PKBSPK")
        builder.apply_constraints(
            [
                DistributeDayOfWeekConstraint(
                    Weekday.THURSDAY, pgys={2: True, 3: False}, tolerance=0
                )
            ]
        )
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BSPKBSPBPKBSPK", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BSPKBSPSPKBSPK")

    def test_distribute_weekends(self):
        # Second weekend can be Barnaby or Kevin. Must be Kevin so his weekend
        # count matches Pippin.
        builder = self._get_builder("BSPKBSPKBP[BK]")
        builder.apply_constraints(
            [DistributeWeekendsConstraint(pgys={2: False, 3: True}, tolerance=0)]
        )
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BSPKBSPKBPB", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BSPKBSPKBPK")

    def test_constrain_weekday(self):
        # Limit Barnaby (PGY2) to zero Thursdays, Kevin must be put in
        builder = self._get_builder("[BK]")
        builder.apply_constraints(
            [
                ConstrainWeekdayConstraint(
                    Weekday.THURSDAY, 0, 0, pgys={2: True, 3: False}
                )
            ]
        )
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("B", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "K")

    def test_constrain_weekday_for_resident(self):
        # Limit Barnaby to zero Thursdays, Kevin must be put in
        builder = self._get_builder("[BK]")
        builder.apply_constraints(
            [LimitWeekdayForResidentConstraint(Weekday.THURSDAY, 0, "Barnaby")]
        )
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("B", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "K")

    def test_minimum_for_resident(self):
        # Set minimum Thursdays for Kevin to 1, he must be put in
        builder = self._get_builder("[BK]")
        builder.apply_constraints(
            [
                SetMinimumForDaysOfWeekForResidentConstraint(
                    {Weekday.THURSDAY}, 1, "Kevin"
                )
            ]
        )
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("B", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "K")

    def test_no_adjacent_weekends(self):
        cases = [
            # Pippin and Kevin work first weekend, Barnaby and Sprocket should
            # do the second
            ("BSPKBSPBK[BP][SK]", 1, "BSPKBSPBKPK", "BSPKBSPBKBS"),
            # Same thing but omit the last Sunday
            ("BSPKBSPBK[BP]", 1, "BSPKBSPBKP", "BSPKBSPBKB"),
            # Similar: Pippin+Kevin work first two weekends
            ("BSPKBSPBKPKBSPBK[BP][SK]", 2, "BSPKBSPBKPKBSPBKPK", "BSPKBSPBKPKBSPBKBS"),
        ]
        for availability, limit, previous, expected in cases:
            with self.subTest(
                availability=availability,
                limit=limit,
                previous=previous,
                expected=expected,
            ):
                builder = self._get_builder(availability)
                builder.apply_constraints([NoAdjacentWeekendsConstraint(limit)])
                builder.set_objectives(
                    [
                        # Try to put Pippin and Kevin back on
                        ChangesFromPreviousSolutionObjective(
                            "fake", ConstraintTest._parse_spec(previous, names=NAMES)
                        )
                    ]
                )
                solution = builder.solve()
                self.assert_solution(solution, expected)
