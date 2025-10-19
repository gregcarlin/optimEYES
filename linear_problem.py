from typing import Optional, Mapping, Sequence

import pulp as pulp

"""
This file provides a simple wrapper around the pulp API
"""

Variable = pulp.LpVariable


class PulpSolution:
    def __init__(self, solved_problem: pulp.LpProblem) -> None:
        assert solved_problem.status != pulp.const.LpStatusNotSolved
        self.problem = solved_problem

    def was_successful(self) -> bool:
        return self.problem.status == pulp.const.LpStatusOptimal

    def get_status(self) -> str:
        return pulp.LpStatus[self.problem.status]

    def get_variables(self) -> Mapping[str, float]:
        return {v.name: v.varValue for v in self.problem.variables()}  # pyright: ignore

    def get_objective_value(self) -> float:
        val = pulp.value(self.problem.objective)
        assert isinstance(val, float)
        return val


class PulpProblem:
    def __init__(
        self, name: str, minimize: bool = True, debug_infeasibility: bool = False
    ) -> None:
        self.name = name
        self.minimize = minimize
        self.debug_infeasibility = debug_infeasibility
        self.var_names = set()
        self.objective_fn = None
        self.constraint_fns = []

    def new_binary_variable(self, name: str) -> Variable:
        assert name not in self.var_names, f"Duplicate variable {name}"
        self.var_names.add(name)
        return pulp.LpVariable(name, cat=pulp.LpBinary)

    def new_integer_variable(
        self,
        name: str,
        lower_bound: Optional[int] = None,
        upper_bound: Optional[int] = None,
    ) -> Variable:
        assert name not in self.var_names, f"Duplicate variable {name}"
        self.var_names.add(name)
        return pulp.LpVariable(name, lower_bound, upper_bound, pulp.LpInteger)

    def new_continuous_variable(
        self,
        name: str,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
    ) -> Variable:
        assert name not in self.var_names, f"Duplicate variable {name}"
        self.var_names.add(name)
        return pulp.LpVariable(name, lower_bound, upper_bound, pulp.LpContinuous)

    def set_objective(self, objective_fn) -> None:
        self.objective_fn = objective_fn

    def add_constraint(self, constraint) -> None:
        self.constraint_fns.append(constraint)
        if self.debug_infeasibility:
            if not self._solve_impl().was_successful():
                raise ValueError("Problem is infeasible with constraint")

    def _get_decision_vars(self, var_name: str, count: int) -> Sequence[Variable]:
        """
        Returns a given number of binary decision variables, where exactly one will be set.
        """
        decision_vars = [
            self.new_binary_variable(f"{var_name}_decision_{i}") for i in range(count)
        ]
        self.add_constraint(sum(decision_vars) == 1)
        return decision_vars

    def max_of(
        self, variables: Sequence[Variable | int], max_possible_val: int, var_name: str
    ) -> Variable:
        """
        Returns a new variable that will be set to the maximum of all the given variables
        See https://math.stackexchange.com/a/3568461
        """
        max_var = self.new_continuous_variable(var_name)
        decision_vars = self._get_decision_vars(var_name, len(variables))
        for var, decision_var in zip(variables, decision_vars):
            self.add_constraint(max_var >= var)
            self.add_constraint(max_var <= var + (1 - decision_var) * max_possible_val)
        return max_var

    def min_of(
        self, variables: Sequence[Variable | int], max_possible_val: int, var_name: str
    ) -> Variable:
        """
        Same as above, but for min.
        """
        min_var = self.new_continuous_variable(var_name)
        decision_vars = self._get_decision_vars(var_name, len(variables))
        for var, decision_var in zip(variables, decision_vars):
            self.add_constraint(min_var <= var)
            self.add_constraint(
                min_var >= var - (1 - decision_var) * (max_possible_val + 1)
            )
        return min_var

    def solve(self) -> PulpSolution:
        assert self.objective_fn is not None, "No objective function specified"
        return self._solve_impl()

    def _solve_impl(self) -> PulpSolution:
        lp_problem = pulp.LpProblem(
            self.name, pulp.LpMinimize if self.minimize else pulp.LpMaximize
        )
        if self.objective_fn is not None:
            lp_problem += self.objective_fn, "Objective"
        for index, constraint_fn in enumerate(self.constraint_fns):
            lp_problem += constraint_fn, f"Constraint_{index}"

        lp_problem.solve(pulp.PULP_CBC_CMD(msg=False))
        return PulpSolution(lp_problem)
