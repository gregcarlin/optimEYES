from typing import override

import pulp as pulp

from optimization.call_problem import CallProblemBuilder
from optimization.linear_problem import Variable, VariableLike, var_sum
from optimization.constraint import Constraint
from optimization.objective import Objective


def _unavailable_days(builder: CallProblemBuilder) -> list[Variable]:
    day_vars = builder.get_day_vars()
    result: list[Variable] = []
    for resident in builder.get_residents().values():
        for day, is_available in enumerate(resident.availability):
            if is_available == 0:
                # Resident is unavailable this day
                result.append(day_vars[resident.name][day])

    return result


class AvailabilityConstraint(Constraint):
    @override
    def get_constraints(self, builder: CallProblemBuilder) -> list[pulp.LpConstraint]:
        return [day_var == 0 for day_var in _unavailable_days(builder)]


class AvailabilityObjective(Objective):
    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        return var_sum(_unavailable_days(builder))

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return builder.get_num_days() * builder.get_num_residents()
