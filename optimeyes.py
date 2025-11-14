from typing import Mapping, Sequence, AbstractSet

import os
from datetime import timedelta
import argparse

from dateutil import Weekday
from call_problem import CallProblemBuilder
from solution import Solution
from structs.output_mode import OutputMode
from structs.resident import Resident
from inputs import (
    START_DATE,
    BUDDY_PERIOD,
    PGY_2_3_GAP,
    SEED,
    get_availability,
    special_handling_for_this_round,
)


def print_availability(availability: AbstractSet[Resident]) -> None:
    print("Availability:")
    num_days = len(next(iter(availability)).availability)
    for i in range(num_days):
        day = START_DATE + timedelta(days=i)
        available_residents = ", ".join(
            f"{resident.name} (VA)" if resident.va[i] == 1 else resident.name
            for resident in availability
            if resident.availability[i] == 1
        )
        print(f"\t{day:%a %m-%d}: {available_residents}")


def _common_attempt(
    availability: AbstractSet[Resident], previous_attempt: list[list[str]] | None
) -> CallProblemBuilder:
    problem = CallProblemBuilder(
        START_DATE,
        BUDDY_PERIOD,
        availability,
        PGY_2_3_GAP,
        debug_infeasibility=False,
        seed=SEED,
    )

    # Ensure even distribution of Saturdays and Sundays
    # problem.evenly_distribute_weekday(Weekday.SATURDAY)
    # problem.evenly_distribute_weekday(Weekday.SUNDAY)

    problem.evenly_distribute_weekends()
    problem.eliminate_adjacent_weekends()

    problem.limit_va_coverage(3)

    special_handling_for_this_round(problem)

    # Minimize Q2 calls
    if previous_attempt is None:
        problem.minimize_q2s()
    else:
        problem.minimize_q2s_and_changes_from_previous_solution(previous_attempt)
    # problem.minimize_va_coverage()
    problem.limit_q2s(2)

    return problem


def base_attempt(
    availability: AbstractSet[Resident], previous_attempt: list[list[str]] | None
) -> Solution | str:
    problem = _common_attempt(availability, previous_attempt)
    return problem.solve()


def distribute_q2s_attempt(
    availability: AbstractSet[Resident],
    tolerance: int,
    max_q2s: int,
    previous_attempt: list[list[str]] | None,
) -> Solution | str:
    problem = _common_attempt(availability, previous_attempt)

    # Evenly distribute q2s
    problem.evenly_distribute_q2s(tolerance)

    # See if we can get a solution where the resident with the most q2s has less
    problem.limit_q2s(max_q2s)

    return problem.solve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=OutputMode,
        choices=list(OutputMode),
        default=OutputMode.INTERACTIVE,
    )
    parser.add_argument("--previous", type=str)
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
    if args.output == OutputMode.INTERACTIVE:
        print_availability(availability)

    previous_attempt = None
    if args.previous:
        with open(args.previous) as f:
            previous_attempt = [line.strip().split(",") for line in f.readlines()]

    base = base_attempt(availability, previous_attempt)
    if isinstance(base, str):
        # TODO relax some constraints and try again
        print(f"Unable to find optimal solution with status: {base}")
        return

    unfairness = base.get_q2_unfairness()

    solutions: list[Solution] = [base]
    """
    for tolerance in range(unfairness - 1, -1, -1):
        attempt = distribute_q2s_attempt(
            availability, tolerance, solutions[-1].get_max_q2s() - 1, previous_attempt
        )
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
    """

    if len(solutions) == 1:
        if args.output == OutputMode.INTERACTIVE:
            print("Optimal solution found!")
        solutions[0].print(args.output, previous_attempt)
        return

    if args.output != OutputMode.INTERACTIVE:
        solutions[0].print(args.output, previous_attempt)
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
        solution.print(OutputMode.INTERACTIVE, previous_attempt)


if __name__ == "__main__":
    main()
