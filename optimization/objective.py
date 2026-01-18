from typing import Literal
from optimization.linear_problem import VariableLike


class Objective:
    def __init__(self, value: VariableLike, max_value: int | None) -> None:
        self.value = value
        self.max_value = max_value

    def then(self, secondary: "Objective") -> "Objective":
        """
        Return an objective that first minimizes/maximizes this objective, and
        then breaks ties with the given secondary objective.
        """
        assert (
            secondary.max_value is not None
        ), "Secondary objective must have max value"
        variable = self.value * (secondary.max_value + 1) + secondary.value
        return Objective(variable, None)
