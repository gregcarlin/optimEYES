import json
from typing import Any, override
from datetime import date
from dataclasses import dataclass

from optimization.constraint import SerializableConstraint, ConstraintRegistry
from optimization.objective import SerializableObjective, ObjectiveRegistry
from structs.project_info import ProjectInfo
from structs.resident import Resident


@dataclass
class Project(ProjectInfo):
    start_date: date
    end_date: date
    buddy_period: list[bool] | None
    availability: list[Resident]
    coverage: list[str]
    seed: int
    constraints: list[SerializableConstraint]
    objectives: list[SerializableObjective]

    @override
    def get_residents(self) -> list[str]:
        return [r.name for r in self.availability]

    @override
    def get_min_pgy(self) -> int:
        return min(r.pgy for r in self.availability)

    @override
    def get_max_pgy(self) -> int:
        return max(r.pgy for r in self.availability)

    @staticmethod
    def deserialize(data: dict[str, Any]) -> "Project":
        start_date = date.fromisoformat(data["start_date"])
        end_date = date.fromisoformat(data["end_date"])

        buddy_period = data.get("buddy_days")
        if buddy_period:
            buddy_period = [bool(day) for day in buddy_period]

        availability = [Resident.deserialize(r) for r in data["availability"]]
        coverage = data["coverage"]

        seed = int(data["seed"])

        constraint_registry = ConstraintRegistry()
        constraints = [
            constraint_registry.deserialize(c["name"], c.get("data", {}))
            for c in data["constraints"]
        ]

        objective_registry = ObjectiveRegistry()
        objectives = [
            objective_registry.deserialize(o["name"], o.get("data", {}))
            for o in data["objectives"]
        ]

        return Project(
            start_date,
            end_date,
            buddy_period,
            availability,
            coverage,
            seed,
            constraints,
            objectives,
        )

    @staticmethod
    def read_from_file(path: str) -> "Project":
        with open(path, "r") as project_file:
            project_data = json.loads(project_file.read())
            return Project.deserialize(project_data)

    def write_to_file(self, path: str) -> None:
        with open(path, "w") as project_file:
            project_data = json.dumps(self.serialize(), indent=1)
            project_file.write(project_data)

    def serialize(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "start_date": f"{self.start_date:%Y-%m-%d}",
            "end_date": f"{self.end_date:%Y-%m-%d}",
        }
        if self.buddy_period:
            data["buddy_days"] = [1 if day else 0 for day in self.buddy_period]
        data.update(
            {
                "availability": [r.serialize() for r in self.availability],
                "coverage": self.coverage,
                "seed": self.seed,
                "constraints": [
                    {"name": c.get_name(), "data": c.serialize()}
                    for c in self.constraints
                ],
                "objectives": [
                    {"name": o.get_name(), "data": o.serialize()}
                    for o in self.objectives
                ],
            }
        )
        return data
