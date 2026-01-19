from typing import Mapping, Sequence, AbstractSet

import os
import json
from datetime import timedelta
import argparse

from dateutil import Weekday
from optimization.call_problem_impl import CallProblemBuilderImpl
from optimization.solution import Solution
from optimization.availability import AvailabilityConstraint, AvailabilityObjective
from optimization.objective import ChangesFromPreviousSolutionObjective, WearinessObjective
from structs.output_mode import OutputMode
from structs.resident import Resident
from project import Project
from inputs import (
    START_DATE,
    BUDDY_PERIOD,
    PGY_2_3_GAP,
    WEARINESS_MAP,
    SEED,
    get_availability,
    # special_handling_for_this_round,
)


"""
class SolutionWithInfo:
    def __init__(self, solution: Solution, optimizes_va: bool) -> None:
        self.solution = solution
        self.optimizes_va = optimizes_va
"""


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


"""
def _setup_problem(
    availability: AbstractSet[Resident],
    soft_availability: bool,
) -> CallProblemBuilder:
    problem = CallProblemBuilder(
        START_DATE,
        BUDDY_PERIOD,
        availability,
        PGY_2_3_GAP,
        WEARINESS_MAP,
        debug_infeasibility=False,
        soft_availability=soft_availability,
        seed=SEED,
    )

    # Ensure even distribution of Saturdays and Sundays
    # problem.evenly_distribute_weekday(Weekday.SATURDAY)
    # problem.evenly_distribute_weekday(Weekday.SUNDAY)

    problem.evenly_distribute_weekends()
    problem.eliminate_adjacent_weekends()

    special_handling_for_this_round(problem)

    return problem


def _setup_objective(
    problem: CallProblemBuilder,
    previous_attempt: list[list[str]] | None,
    prioritize_va: bool,
) -> None:
    q2s_objective = problem.get_q2s_objective()
    va_objective = problem.get_va_coverage_objective()
    if prioritize_va:
        objective = va_objective.then(q2s_objective)
    else:
        objective = q2s_objective.then(va_objective)
    objective = objective.then(problem.get_weariness_objective())
    # Minimize Q2 calls
    if previous_attempt is not None:
        changes_objective = problem.get_changes_from_previous_solution_objective(
            previous_attempt
        )
        objective = objective.then(changes_objective)
    problem.set_objective(objective)


def common_attempt(
    availability: AbstractSet[Resident],
    previous_attempt: list[list[str]] | None,
    prioritize_va: bool,
    soft_availability: bool,
) -> CallProblemBuilder:
    problem = _setup_problem(availability, soft_availability)
    _setup_objective(problem, previous_attempt, prioritize_va)
    return problem


def distribute_q2s_attempt(
    problem: CallProblemBuilder,
    tolerance: int,
    max_q2s: int,
) -> Solution | str:
    # Evenly distribute q2s
    problem.evenly_distribute_q2s(tolerance)

    # See if we can get a solution where the resident with the most q2s has less
    problem.limit_q2s(max_q2s)

    return problem.solve()
"""


"""
def find_alternatives(
    base: Solution,
    availability: AbstractSet[Resident],
    previous_attempt: list[list[str]] | None,
    prioritize_va: bool,
) -> list[SolutionWithInfo]:
    solutions: list[Solution] = [base]
    unfairness = base.get_q2_unfairness()
    for tolerance in range(unfairness - 1, -1, -1):
        problem = common_attempt(availability, previous_attempt, prioritize_va, False)
        attempt = distribute_q2s_attempt(
            problem, tolerance, solutions[-1].get_max_q2s() - 1
        )
        if isinstance(attempt, str):
            # No solution found, give up
            break
        if attempt.get_total_q2s() <= solutions[-1].get_total_q2s():
            # Note: q2 count should never actually be less than, but it may be
            # equal. In this case, our new solution has the same number of q2
            # calls, but distributes them more evenly.
            solutions = solutions[:-1]
            solutions.append(attempt)
        else:
            solutions.append(attempt)
    return [SolutionWithInfo(solution, prioritize_va) for solution in solutions]
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
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

    with open(args.project, "r") as project_file:
        project_data = json.loads(project_file.read())
        project = Project.deserialize(project_data)

    builder = CallProblemBuilderImpl(project, availability)
    builder.apply_constraints([AvailabilityConstraint()])
    builder.apply_constraints(project.constraints)
    builder.set_objectives(project.objectives)

    # TODO generalize into objective with metric
    weariness_objs = [obj for obj in project.objectives if isinstance(obj, WearinessObjective)]
    assert len(weariness_objs) <= 1, "Multiple weariness objectives not yet supported"
    weariness_map = None if weariness_objs == [] else weariness_objs[0].weariness_map

    previous_objs = [obj for obj in project.objectives if isinstance(obj, ChangesFromPreviousSolutionObjective)]
    assert len(previous_objs) <= 1, "Multiple previous result objectives not supported"
    previous_data = None if previous_objs == [] else previous_objs[0].read_data()

    if args.output == OutputMode.INTERACTIVE:
        print("Solving for base result")
    base_result = builder.solve()
    if isinstance(base_result, str):
        print(f"Unable to find optimal solution with status: {base_result}")
        # Re-run with soft availability, see if it can identify any scheduling conflicts
        print(f"Attempting to identify the problem")
        # While including the other objectives (as secondaries) wouldn't
        # meaningfully change the resulting hint, it makes finding it
        # significantly slower. So we just focus on the availability objective.
        debug_builder = CallProblemBuilderImpl(project, availability)
        debug_builder.apply_constraints(project.constraints)
        debug_builder.set_objectives([AvailabilityObjective()])
        debug_result = debug_builder.solve()
        if isinstance(debug_result, str):
            print("Unable to generate hints for failed attempt, you're on your own")
        else:
            violations = debug_result.get_availability_violations()
            assert len(violations) > 0, "Error calculating availability violations"
            print(
                f"Hint (may not be accurate): Try checking the schedule around the following days and/or residents:"
            )
            for day, residents in violations.items():
                date = START_DATE + timedelta(days=day)
                residents_str = ", ".join(residents)
                print(f"\t{date:%a %m-%d}: {residents_str}")
        return

    base_result.print(OutputMode.INTERACTIVE, previous_data, weariness_map)
    """
    if args.output == OutputMode.INTERACTIVE:
        print("Considering alternative solutions")
    solutions = find_alternatives(base_q2, availability, previous_attempt, False)

    if args.output == OutputMode.INTERACTIVE:
        print("Considering VA coverage")
    base_va = common_attempt(availability, previous_attempt, True, False).solve()
    assert not isinstance(
        base_va, str
    ), "Found result when prioritizing Q2s but failed when prioritizing VA, this shouldn't happen"
    if base_va.get_va_covered_days() < base_q2.get_va_covered_days():
        if args.output == OutputMode.INTERACTIVE:
            print("Considering alternative VA solutions")
        solutions.extend(
            find_alternatives(base_va, availability, previous_attempt, True)
        )

    return solutions
    if len(solutions) == 1:
        if args.output == OutputMode.INTERACTIVE:
            print("Optimal solution found!")
        solutions[0].solution.print(args.output, previous_attempt)
        return

    if args.output != OutputMode.INTERACTIVE:
        solutions[0].solution.print(args.output, previous_attempt)
        return

    print(f"Found {len(solutions)} potential solutions:")
    width = 80
    try:
        width = os.get_terminal_size().columns
    except OSError:
        # Thrown if output is not directly to a terminal (eg. it's piped to a file)
        pass
    for i, solution in enumerate(solutions):
        text = f"Solution {i+1} (optimizes for {'VA coverage' if solution.optimizes_va else 'Q2s'}):"
        buffer = int((width - len(text)) / 2) * "="
        print(f"{buffer}{text}{buffer}")
        solution.solution.print(OutputMode.INTERACTIVE, previous_attempt)
    """


if __name__ == "__main__":
    main()
