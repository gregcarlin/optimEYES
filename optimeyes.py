from typing import Mapping, Sequence, AbstractSet

import os
from datetime import date, timedelta

from dateutil import Weekday
from call_problem import CallProblemBuilder, Resident
from input import InputBuilder
from solution import Solution

START_DATE = date.fromisoformat("2025-07-01")
# fmt: off
RESIDENTS = {
    Resident(
        name="Sophia",
        pgy=2,
        availability=[
            0, 1, 0, 0, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
        ],
    ),
    Resident(
        name="Paris",
        pgy=2,
        availability=[
            0, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
        ],
    ),
    Resident(
        name="Keir",
        pgy=2,
        availability=[
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1,
        ],
    ),
}
# fmt: on


def print_availability(availability: AbstractSet[Resident]) -> None:
    print("Availability:")
    num_days = len(next(iter(availability)).availability)
    for i in range(num_days):
        day = START_DATE + timedelta(days=i)
        available_residents = ", ".join(
            resident.name for resident in availability if resident.availability[i] == 1
        )
        print(f"\t{day:%a %m-%d}: {available_residents}")


def base_attempt(availability: AbstractSet[Resident]) -> Solution | str:
    problem = CallProblemBuilder(START_DATE, availability, debug_infeasibility=False)

    # Ensure even distribution of Saturdays and Sundays
    problem.evenly_distribute_weekday(Weekday.SATURDAY)
    problem.evenly_distribute_weekday(Weekday.SUNDAY)

    # Minimize Q2 calls
    problem.minimize_q2s()

    return problem.solve()


def distribute_q2s_attempt(
    availability: AbstractSet[Resident], tolerance: int
) -> Solution | str:
    problem = CallProblemBuilder(START_DATE, availability)

    # Ensure even distribution of Saturdays and Sundays
    problem.evenly_distribute_weekday(Weekday.SATURDAY)
    problem.evenly_distribute_weekday(Weekday.SUNDAY)

    # Minimize Q2 calls
    problem.minimize_q2s()

    # Evenly distribute q2s
    problem.evenly_distribute_q2s(tolerance)

    return problem.solve()


def main() -> None:
    input = InputBuilder(START_DATE, RESIDENTS)
    input.assign_to_day_of_week("Sophia", Weekday.WEDNESDAY, "2025-07-01", "2025-07-29")
    availability = input.build()

    print_availability(availability)

    base = base_attempt(availability)
    if isinstance(base, str):
        # TODO relax some constraints and try again
        print("Unable to find optimal solution with status: {base}")
        return

    unfairness = base.get_q2_unfairness()

    solutions = [base]
    for tolerance in range(unfairness - 1, -1, -1):
        attempt = distribute_q2s_attempt(availability, tolerance)
        if isinstance(attempt, str):
            # No solution found, give up
            break
        if attempt.get_objective_value() <= solutions[-1].get_objective_value():
            # Note: objective value should never actually be less than, but it
            # may be equal.  In this case, our new solution has the same number
            # of q2 calls, but distributes them more evenly.
            solutions = solutions[:-1]
            solutions.append(attempt)
        else:
            solutions.append(attempt)

    if len(solutions) == 1:
        print("Optimal solution found!")
        solutions[0].print()
        return

    print(f"Found {len(solutions)} potential solutions:")
    width = os.get_terminal_size().columns
    for i, solution in enumerate(solutions):
        text = f"Solution {i+1}:"
        buffer = int((width - len(text)) / 2) * "="
        print(f"{buffer}{text}{buffer}")
        solution.print()


if __name__ == "__main__":
    main()
