from optimization.tests.test_base import TestBase, NAMES
from optimization.objective import (
    ChangesFromPreviousSolutionObjective,
    Q2Objective,
    VACoverageObjective,
    WearinessObjective,
)


class ObjectiveTest(TestBase):
    def test_q2_objective(self) -> None:
        # Use Kevin to minimize Q2s
        builder = self._get_builder("BP[BK]")
        builder.set_objectives(
            [
                Q2Objective(),
            ]
        )
        solution = builder.solve()
        self.assert_solution(solution, "BPK")

    def test_changes_objective(self) -> None:
        cases = [
            # Use Kevin anyway to avoid Pippin working twice in a row
            ("BP[PK]", "BPP", "BPK"),
            # Exactly match previous
            ("BS[PK]", "BSP", "BSP"),
        ]
        for availability, previous, expected in cases:
            with self.subTest(
                availability=availability, previous=previous, expected=expected
            ):
                builder = self._get_builder(availability)
                builder.set_objectives(
                    [
                        ChangesFromPreviousSolutionObjective(
                            "fake", TestBase._parse_spec(previous, names=NAMES)
                        )
                    ]
                )
                solution = builder.solve()
                self.assert_solution(solution, expected)

    def test_va(self):
        # Barnaby is at the VA, use Kevin
        builder = self._get_builder("[BK]", va_spec="B")
        builder.set_objectives([VACoverageObjective()])
        solution = builder.solve()
        self.assert_solution(solution, "K")

    def test_weariness(self):
        # Use Kevin to minimize weariness
        builder = self._get_builder("[BK]SB")
        builder.set_objectives([WearinessObjective({2: 100})])
        solution = builder.solve()
        self.assert_solution(solution, "KSB")
