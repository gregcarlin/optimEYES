from typing import Optional, Mapping
import pulp as pulp

"""
This file provides a simple wrapper around the pulp API
"""


def new_binary_variable(name: str):
    return pulp.LpVariable(name, cat=pulp.LpBinary)


def new_integer_variable(
    name: str, lower_bound: Optional[int] = None, upper_bound: Optional[int] = None
):
    return pulp.LpVariable(name, lower_bound, upper_bound, pulp.LpInteger)


def new_continuous_variable(
    name: str, lower_bound: Optional[float] = None, upper_bound: Optional[float] = None
):
    return pulp.LpVariable(name, lower_bound, upper_bound, pulp.LpContinuous)


class PulpSolution:
    def __init__(self, solved_problem: pulp.LpProblem) -> None:
        assert solved_problem.status != pulp.const.LpStatusNotSolved
        self.problem = solved_problem

    def was_successful(self) -> bool:
        return self.problem.status == pulp.const.LpStatusOptimal

    def get_status(self) -> str:
        return pulp.LpStatus[self.problem.status]

    def get_variables(self) -> Mapping[str, float]:
        return {v.name: v.varValue for v in self.problem.variables()} # pyright: ignore

    def get_objective_value(self):
        return pulp.value(self.problem.objective)


class PulpProblem:
    def __init__(self, name: str, minimize: bool = True) -> None:
        self.lp_problem = pulp.LpProblem(name, pulp.LpMinimize if minimize else pulp.LpMaximize)
        self.objective_fn = None
        self.constraint_fns = []
        self.solved = False

    def set_objective(self, objective_fn) -> None:
        assert not self.solved
        self.objective_fn = objective_fn

    def add_constraint(self, constraint) -> None:
        assert not self.solved
        self.constraint_fns.append(constraint)

    def solve(self) -> PulpSolution:
        assert self.objective_fn is not None, "No objective function specified"

        self.lp_problem += self.objective_fn, "Objective"
        for index, constraint_fn in enumerate(self.constraint_fns):
            self.lp_problem += constraint_fn, f"Constraint_{index}"

        self.lp_problem.solve(pulp.COIN(msg=0))
        self.solved = True
        return PulpSolution(self.lp_problem)
