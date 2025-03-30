import os

from datetime import date, timedelta

from dateutil import Weekday
from call_problem import CallProblemBuilder
from input import InputBuilder

START_DATE = date.fromisoformat("2025-07-01")
# fmt: off
RESIDENT_AVAILABILITY = {
    "Sophia": [
        0, 1, 0, 0, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
    ],
    "Paris": [
        0, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
    ],
    "Keir": [
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1,
    ],
}
# fmt: on


def main() -> None:
    input = InputBuilder(START_DATE, RESIDENT_AVAILABILITY)
    input.assign_to_day_of_week("Sophia", Weekday.WEDNESDAY)

    problem = CallProblemBuilder(START_DATE, input.get_availability())

    # Ensure even distribution of Saturdays and Sundays
    problem.evenly_distribute_weekday(Weekday.SATURDAY)
    problem.evenly_distribute_weekday(Weekday.SUNDAY)

    # TODO if first solution fails, relax tolerance here
    problem.evenly_distribute_q2s()

    # Minimize Q2 calls
    problem.minimize_q2s()

    solution = problem.solve()

    # Overall status, were we able to find a solution?
    if isinstance(solution, str):
        width = os.get_terminal_size().columns
        print("=" * width)
        print(f"WARNING: Unable to find optimal solution with status: {solution}")
        print("=" * width)
        return
    else:
        print("Optimal solution found!")

    for day, resident in enumerate(solution.get_assignments()):
        date = START_DATE + timedelta(days=day)
        print(f"\t{date:%a %m-%d}: {resident}")

    print("Total Q2 calls = ", solution.get_objective_value())

    print("Per resident stats:")
    calls = solution.get_calls_per_resident()
    saturdays = solution.get_saturdays()
    sundays = solution.get_sundays()
    q2s = solution.get_q2s_per_resident()
    for resident in RESIDENT_AVAILABILITY.keys():
        print(f"\t{resident}")
        print(f"\t\tCalls = {calls[resident]}")
        print(f"\t\tSaturdays = {saturdays[resident]}")
        print(f"\t\tSundays = {sundays[resident]}")
        print(f"\t\tQ2s = {q2s[resident]}")


if __name__ == "__main__":
    main()
