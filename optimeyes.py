from typing import Mapping, Sequence, AbstractSet

import os
from datetime import timedelta
import argparse

from dateutil import Weekday
from call_problem import CallProblemBuilder, Resident
from solution import Solution
from inputs import START_DATE, BUDDY_PERIOD, PGY_2_3_GAP, get_availability


def print_availability(availability: AbstractSet[Resident]) -> None:
    print("Availability:")
    num_days = len(next(iter(availability)).availability)
    for i in range(num_days):
        day = START_DATE + timedelta(days=i)
        available_residents = ", ".join(
            resident.name for resident in availability if resident.availability[i] == 1
        )
        print(f"\t{day:%a %m-%d}: {available_residents}")


def _common_attempt(availability: AbstractSet[Resident]) -> CallProblemBuilder:
    problem = CallProblemBuilder(
        START_DATE, BUDDY_PERIOD, availability, PGY_2_3_GAP, debug_infeasibility=False
    )

    # Ensure even distribution of Saturdays and Sundays
    problem.evenly_distribute_weekday(Weekday.SATURDAY)
    problem.evenly_distribute_weekday(Weekday.SUNDAY)

    problem.eliminate_adjacent_weekends()

    # Minimize Q2 calls
    problem.minimize_q2s()

    problem.limit_weekday("Sophia", Weekday.SATURDAY, 3)
    problem.limit_weekday("Sophia", Weekday.SUNDAY, 3)

    return problem


def base_attempt(availability: AbstractSet[Resident]) -> Solution | str:
    problem = _common_attempt(availability)
    return problem.solve()


def distribute_q2s_attempt(
    availability: AbstractSet[Resident], tolerance: int
) -> Solution | str:
    problem = _common_attempt(availability)

    # Evenly distribute q2s
    problem.evenly_distribute_q2s(tolerance)

    return problem.solve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    inputs = get_availability()
    availability_or_errors = inputs.build()
    if isinstance(availability_or_errors, list):
        print("Availability is invalid. Found the following errors:")
        for error in availability_or_errors:
            print(error)
        return

    availability = availability_or_errors
    if not args.csv:
        print_availability(availability)

    base = base_attempt(availability)
    if isinstance(base, str):
        # TODO relax some constraints and try again
        print(f"Unable to find optimal solution with status: {base}")
        return

    unfairness = base.get_q2_unfairness()

    solutions: list[Solution] = [base]
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
        solutions[0].print(args.csv)
        return

    if args.csv:
        solutions[0].print(True)
        return

    print(f"Found {len(solutions)} potential solutions:")
    width = 80
    try:
        width = os.get_terminal_size().columns
    except OSError:
        # Thrown if output is not directly to a terminal (eg. it's piped to a file)
        pass
    for i, solution in enumerate(solutions):
        text = f"Solution {i+1}:"
        buffer = int((width - len(text)) / 2) * "="
        print(f"{buffer}{text}{buffer}")
        solution.print()


if __name__ == "__main__":
    main()
