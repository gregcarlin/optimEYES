import math
from typing import Any, override, TypeVar, Generic, Sequence
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path

from optimization.linear_problem import VariableLike
from optimization.call_problem import CallProblemBuilder
from optimization.metric import SummaryMetric, ResidentMetric, DetailMetric
from structs.field import (
    Field,
    StringField,
    FileField,
)
from structs.project_info import ProjectInfo


class Objective(ABC):
    @abstractmethod
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        pass

    @abstractmethod
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        pass


TFields = TypeVar("TFields", bound="tuple[Field, ...]")


class SerializableObjective(Objective, Generic[TFields]):
    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def human_name() -> str:
        pass

    @staticmethod
    @abstractmethod
    def default(project: ProjectInfo) -> Objective:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: dict[str, Any]) -> Objective:
        pass

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def fields(self, project: ProjectInfo) -> TFields:
        pass

    @classmethod
    @abstractmethod
    def from_fields(cls, fields: TFields) -> "SerializableObjective":
        pass


class NoArgSerializableObjective(SerializableObjective[tuple[()]]):
    @classmethod
    @override
    def deserialize(cls, data: dict[str, Any]) -> Objective:
        return cls()

    @override
    def serialize(self) -> dict[str, Any]:
        return {}

    @override
    def fields(self, project: ProjectInfo) -> tuple[()]:
        return ()

    @classmethod
    @override
    def from_fields(cls, fields: tuple[()]) -> "SerializableObjective":
        return cls()


class Q2Objective(NoArgSerializableObjective):
    @staticmethod
    @override
    def get_name() -> str:
        return "q2s"

    @staticmethod
    @override
    def human_name() -> str:
        return "Minimize Q2s"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Objective:
        return Q2Objective()

    @override
    def description(self) -> str:
        return Q2Objective.human_name()

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        q2s_dict = builder.get_qn_vars(2)
        q2s = sum(v for vs in q2s_dict.values() for v in vs)
        assert isinstance(q2s, VariableLike)
        return q2s

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return math.ceil(builder.get_num_days() / 2.0) * builder.get_num_residents()


class ChangesFromPreviousSolutionObjective(
    SerializableObjective[tuple[FileField]], SummaryMetric, DetailMetric
):
    def __init__(self, path: str, data: list[list[str]]) -> None:
        self.path = path
        self.data = data

    @staticmethod
    @override
    def get_name() -> str:
        return "changes_from_previous_solution"

    @staticmethod
    @override
    def human_name() -> str:
        return "Minimize changes from another solution"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Objective:
        return ChangesFromPreviousSolutionObjective("", [])

    @override
    def description(self) -> str:
        return f"Minimize changes from the solution in {Path(self.path).name}"

    @classmethod
    @override
    def deserialize(cls, data: dict[str, Any]) -> Objective:
        per_day_data: list[str] = data["data"]
        full_data = [datum.split(",") for datum in per_day_data]
        return ChangesFromPreviousSolutionObjective(str(data["path"]), full_data)

    @override
    def serialize(self) -> dict[str, Any]:
        data = [",".join(day) for day in self.data]
        return {"path": self.path, "data": data}

    @override
    def fields(self, project: ProjectInfo) -> tuple[FileField]:
        return (FileField(self.path, "Path to solution file"),)

    @classmethod
    @override
    def from_fields(cls, fields: tuple[FileField]) -> "SerializableObjective":
        path = fields[0].value
        data = ChangesFromPreviousSolutionObjective.read_data(path)
        return ChangesFromPreviousSolutionObjective(path, data)

    @staticmethod
    def read_data(path) -> list[list[str]]:
        with open(path, "r") as result_file:
            return [line.strip().split(",") for line in result_file.readlines()]

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        previous_result = self.data

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

    @override
    def summary_metric_header(self) -> str:
        return "Changes from previous"

    @override
    def summary_metric(self, assignments: Sequence[Sequence[str]]) -> str:
        return str(
            sum(
                0 if sorted(current) == sorted(prev) else 1
                for day, (current, prev) in enumerate(zip(assignments, self.data))
            )
        )

    @override
    def detail_metric_header(self) -> str:
        return "Previous"

    @override
    def detail_metric_tooltip(self) -> str:
        return f"Resident(s) assigned in {Path(self.path).name}, if different"

    @override
    def detail_metric(self, assignments: Sequence[Sequence[str]]) -> list[str]:
        return [
            "" if sorted(current) == sorted(prev) else ", ".join(prev)
            for day, (current, prev) in enumerate(zip(assignments, self.data))
        ]


class VACoverageObjective(NoArgSerializableObjective):
    @staticmethod
    @override
    def get_name() -> str:
        return "va_coverage"

    @staticmethod
    @override
    def human_name() -> str:
        return "Minimize VA coverage"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Objective:
        return VACoverageObjective()

    @override
    def description(self) -> str:
        return VACoverageObjective.human_name()

    @override
    def get_objective(self, builder: CallProblemBuilder) -> VariableLike:
        va_vars = sum(builder.get_va_vars())
        assert isinstance(va_vars, VariableLike)
        return va_vars

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return builder.get_num_days() * builder.get_num_residents()


# TODO improve field spec
class WearinessObjective(SerializableObjective[tuple[StringField]], ResidentMetric):
    def __init__(self, weariness_map: dict[int, int]) -> None:
        self.weariness_map = weariness_map

    @staticmethod
    @override
    def get_name() -> str:
        return "weariness"

    @staticmethod
    @override
    def human_name() -> str:
        return "Minimize the maximum weariness score across residents"

    @staticmethod
    @override
    def default(project: ProjectInfo) -> Objective:
        return WearinessObjective({3: 10, 4: 5, 5: 3, 6: 2, 7: 1})

    @override
    def description(self) -> str:
        return WearinessObjective.human_name()

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
    def fields(self, project: ProjectInfo) -> tuple[StringField]:
        return (
            StringField(
                ",".join(f"{k}={v}" for k, v in self.weariness_map.items()),
                "Weariness map",
            ),
        )

    @classmethod
    @override
    def from_fields(cls, fields: tuple[StringField]) -> "SerializableObjective":
        weariness_map: dict[int, int] = {}
        for entry in fields[0].value.split(","):
            k, v = entry.split("=")
            weariness_map[int(k)] = int(v)
        return WearinessObjective(weariness_map)

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
        problem = builder.get_problem()
        return problem.max_of(
            weariness_scores,
            max_possible_weariness,
            f"max_weariness_{problem.get_var_name_index()}",
        )

    @override
    def get_max_value(self, builder: CallProblemBuilder) -> int:
        return sum(
            math.ceil(builder.get_num_days() / n) * incr
            for n, incr in self.weariness_map.items()
        )

    @override
    def resident_metric_header(self) -> str:
        return "Weariness"

    def _get_qns_per_resident(
        self, assignments: Sequence[Sequence[str]], n: int
    ) -> dict[str, int]:
        all_residents = set([r for rs in assignments for r in rs])
        result = {resident: 0 for resident in all_residents}
        for day in range(len(assignments) - n):
            for resident in set(assignments[day]).intersection(
                set(assignments[day + n])
            ):
                result[resident] += 1
        return result

    @staticmethod
    def _fmt_weariness(score: int, breakdown: dict[int, int]) -> str:
        breakdown_str = ", ".join(
            f"{breakdown[n]}x Q{n}"
            for n in sorted(breakdown.keys())
            if breakdown[n] > 0
        )
        return f"{score} ({breakdown_str})"

    @override
    def resident_metric(self, assignments: Sequence[Sequence[str]]) -> dict[str, str]:
        all_residents = set([r for rs in assignments for r in rs])
        scores: dict[str, int] = {resident: 0 for resident in all_residents}
        breakdown: dict[str, dict[int, int]] = {
            resident: {} for resident in all_residents
        }
        for n, incr in self.weariness_map.items():
            for resident, qns in self._get_qns_per_resident(assignments, n).items():
                scores[resident] += qns * incr
                breakdown[resident][n] = qns
        return {
            r: WearinessObjective._fmt_weariness(scores[r], breakdown[r])
            for r in all_residents
        }


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

    def deserialize(self, name: str, data: dict[str, Any]) -> SerializableObjective:
        return self.objectives[name].deserialize(data)


def combine_objectives(
    builder: CallProblemBuilder,
    objectives: list[Objective] | list[SerializableObjective],
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
