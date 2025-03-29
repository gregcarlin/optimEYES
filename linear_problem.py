from pulp import *
from typing import Optional

"""
This file provides a simple wrapper around the pulp API
"""


def new_binary_variable(name: str):
    return LpVariable(name, cat=LpBinary)


def new_integer_variable(
    name: str, lower_bound: Optional[int] = None, upper_bound: Optional[int] = None
):
    return LpVariable(name, lower_bound, upper_bound, LpInteger)


def new_continuous_variable(
    name: str, lower_bound: Optional[int] = None, upper_bound: Optional[int] = None
):
    return LpVariable(name, lower_bound, upper_bound, LpContinuous)


class PulpSolution:
    def __init__(self, solved_problem: LpProblem) -> None:
        assert solved_problem.status != const.LpStatusNotSolved
        self.problem = solved_problem

    def was_successful(self) -> bool:
        return self.problem.status == const.LpStatusOptimal

    def get_status(self) -> str:
        return LpStatus[self.problem.status]

    def get_variables(self) -> Dict[str, float]:
        return {v.name: v.varValue for v in self.problem.variables()}

    def get_objective_value(self):
        return value(self.problem.objective)


class PulpProblem:
    def __init__(self, name: str, minimize: bool = True) -> None:
        self.lp_problem = LpProblem(name, LpMinimize if minimize else LpMaximize)
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

        self.lp_problem.solve(COIN(msg=0))
        self.solved = True
        return PulpSolution(self.lp_problem)
