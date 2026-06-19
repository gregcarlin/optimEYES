from datetime import date

from optimization.tests.test_base import TestBase, NAMES
from optimization.constraint import (
    DistributeWithinPGYConstraint,
    DistributeDayOfWeekConstraint,
    DistributeWeekendsConstraint,
    ConstrainWeekdayConstraint,
    LimitWeekdayForResidentConstraint,
    SetMinimumForDaysOfWeekForResidentConstraint,
    NoAdjacentWeekendsConstraint,
    ConstrainPGYConstraint,
    LimitVACoverageConstraint,
    DistributeQ2sConstraint,
    LimitQ2sConstraint,
    LimitTotalQ2sConstraint,
    LimitPGY23GapConstraint,
    LimitResidentBetweenDatesConstraint,
)
from optimization.objective import ChangesFromPreviousSolutionObjective
from dateutil import Weekday


class ConstraintTest(TestBase):
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
                        ChangesFromPreviousSolutionObjective(
                            "fake", ConstraintTest._parse_spec(previous, names=NAMES)
                        )
                    ]
                )
                solution = builder.solve()
                self.assert_solution(solution, expected)

    def test_constrain_pgy(self):
        # Constrain PGY3 (Kevin) to have exactly 1 call, must be put in
        builder = self._get_builder("[BK]P")
        builder.apply_constraints([ConstrainPGYConstraint(3, 1, 1)])
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BP", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "KP")

    def test_limit_va(self):
        # Barnaby is at the VA, use Kevin
        builder = self._get_builder("[BK]", va_spec="B")
        builder.apply_constraints([LimitVACoverageConstraint(0)])
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

    def test_distribute_q2s(self):
        # Use Kevin to avoid Q2 for Barnaby
        builder = self._get_builder("BS[BK]")
        builder.apply_constraints([DistributeQ2sConstraint(0)])
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BSB", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BSK")

    def test_limit_q2s(self):
        # Use Kevin to avoid Q2 for Barnaby
        builder = self._get_builder("BS[BK]")
        builder.apply_constraints([LimitQ2sConstraint(0)])
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BSB", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BSK")

    def test_limit_total_q2s(self):
        # Use Kevin to avoid Q2 for Barnaby
        builder = self._get_builder("BS[BK]")
        builder.apply_constraints([LimitTotalQ2sConstraint(0)])
        builder.set_objectives(
            [
                # Try to put Barnaby in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("BSB", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BSK")

    def test_limit_pgy_23_gap(self):
        # Barnaby is the PGY2 with the most call (1), Pippin (PGY3) already has
        # 1, but this constraint requires Kevin (PGY3) to also be assigned
        builder = self._get_builder("PB[PK]")
        builder.apply_constraints([LimitPGY23GapConstraint(0)])
        builder.set_objectives(
            [
                # Try to put Pippin in that day
                ChangesFromPreviousSolutionObjective(
                    "fake", ConstraintTest._parse_spec("PBP", names=NAMES)
                )
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "PBK")

    def test_limit_between_dates(self):
        # Limit Barnaby to 0, must use Kevin
        builder = self._get_builder("[BK]")
        builder.apply_constraints(
            [
                LimitResidentBetweenDatesConstraint(
                    "Barnaby", 0, date(2026, 1, 1), date(2026, 1, 1)
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
