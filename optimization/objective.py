import math
from typing import Literal, Any, override
from abc import ABC, abstractmethod
from collections import defaultdict

from optimization.linear_problem import VariableLike
from optimization.call_problem import CallProblemBuilder


class Objective(ABC):
    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: dict[str, Any]) -> "Objective":
        pass

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        pass

    @abstractmethod
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        pass


class NoArgObjective(Objective):
    @classmethod
    @override
    def deserialize(cls, data: dict[str, Any]) -> Objective:
        return cls()

    @override
    def serialize(self) -> dict[str, Any]:
        return {}


class Q2Objective(NoArgObjective):
    @staticmethod
    @override
    def get_name() -> str:
        return "q2s"

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        q2s_dict = builder.get_qn_vars(2)
        q2s = sum(v for vs in q2s_dict.values() for v in vs)
        assert isinstance(q2s, VariableLike)
        return q2s

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return math.ceil(builder.get_num_days() / 2.0) * builder.get_num_residents()


class ChangesFromPreviousSolutionObjective(Objective):
    def __init__(self, path: str) -> None:
        self.path = path

    @staticmethod
    @override
    def get_name() -> str:
        return "changes_from_previous_solution"

    @classmethod
    @override
    def deserialize(cls, data: dict[str, Any]) -> Objective:
        return ChangesFromPreviousSolutionObjective(str(data["path"]))

    @override
    def serialize(self) -> dict[str, Any]:
        return {"path": self.path}

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        # TODO load previous result
        previous_result: list[list[str]] = []
        is_changed_vars = []
        for i, previous in enumerate(previous_result):
            if len(previous) != 1:
                raise ValueError(
                    "Minimizing changes from previous not yet supported for buddy call"
                )
            is_changed_vars.append(1 - builder.get_day_vars()[previous[0]][i])

        result = sum(is_changed_vars)
        assert isinstance(result, VariableLike)
        return result

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return builder.get_num_days()


class VACoverageObjective(NoArgObjective):
    @staticmethod
    @override
    def get_name() -> str:
        return "va_coverage"

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        va_vars = sum(builder.get_va_vars())
        assert isinstance(va_vars, VariableLike)
        return va_vars

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return builder.get_num_days() * builder.get_num_residents()


class WearinessObjective(Objective):
    def __init__(self, weariness_map: dict[int, int]) -> None:
        self.weariness_map = weariness_map

    @staticmethod
    @override
    def get_name() -> str:
        return "weariness"

    @classmethod
    @override
    def deserialize(cls, data: dict[str, Any]) -> Objective:
        weariness_map: dict[int, int] = {}
        for entry in data["map"].split(","):
            k, v = entry.split("=")
            weariness_map[int(k)] = int(v)
        return WearinessObjective(weariness_map)

    @override
    def serialize(self) -> dict[str, Any]:
        map_str = ",".join(
            f"{k}={self.weariness_map[k]}" for k in sorted(self.weariness_map.keys())
        )
        return {"map": map_str}

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        # resident -> qn -> count of that qn
        qns_per_resident: dict[str, dict[int, VariableLike]] = defaultdict(dict)
        for n, incr in self.weariness_map.items():
            qn_dict = builder.get_qn_vars(n)
            for resident, qns in qn_dict.items():
                qns_per_resident[resident][n] = sum(qns)

        weariness_scores: list[VariableLike] = []
        for resident, qns_by_n in qns_per_resident.items():
            weariness_scores.append(
                sum(qns * self.weariness_map[n] for n, qns in qns_by_n.items())
            )

        max_possible_weariness = self.get_max_value(builder)
        return builder.get_problem().max_of(
            weariness_scores, max_possible_weariness, "max_weariness"
        )

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return sum(
            math.ceil(builder.get_num_days() / n) * incr
            for n, incr in self.weariness_map.items()
        )


class ObjectiveRegistry:
    def __init__(self) -> None:
        self.objectives = {
            o.get_name(): o
            for o in [
                Q2Objective,
                ChangesFromPreviousSolutionObjective,
                VACoverageObjective,
                WearinessObjective,
            ]
        }

    def deserialize(self, name: str, data: dict[str, Any]) -> Objective:
        return self.objectives[name].deserialize(data)


def combine_objectives(
    builder: CallProblemBuilder, objectives: list[Objective]
) -> VariableLike:
    """
    Return an objective that first targets the first objective in the list,
    then breaks ties with the next one in the list, etc. Only works if the
    objective's variables are constrained to be integers (not floats).
    """
    assert objectives != [], "At least one objective must be specified"
    variable = objectives[0].get_objective(builder)
    for objective in objectives[1:]:
        variable = variable * (
            objective.get_max_value(builder) + 1
        ) + objective.get_objective(builder)
    return variable
