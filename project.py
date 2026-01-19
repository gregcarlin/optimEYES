from typing import Any, AbstractSet
from datetime import date
from dataclasses import dataclass

from optimization.constraint import Constraint, ConstraintRegistry
from optimization.objective import Objective, ObjectiveRegistry
from structs.resident import Resident


@dataclass
class Project:
    start_date: date
    end_date: date
    buddy_period: tuple[date, date] | None
    availability: AbstractSet[Resident]
    pgy_2_3_gap: int
    seed: int
    constraints: list[Constraint]
    objectives: list[Objective]

    @staticmethod
    def deserialize(data: dict[str, Any]) -> "Project":
        start_date = date.fromisoformat(data["start_date"])
        end_date = date.fromisoformat(data["end_date"])

        if "buddy_period_start_date" and "buddy_period_end_date" in data:
            buddy_start = date.fromisoformat(data["buddy_period_start_date"])
            buddy_end = date.fromisoformat(data["buddy_period_end_date"])
            buddy_period = (buddy_start, buddy_end)
        else:
            buddy_period = None

        # TODO availability
        availability = set()

        pgy_2_3_gap = int(data["pgy_2_3_gap"])
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
            pgy_2_3_gap,
            seed,
            constraints,
            objectives,
        )

    def serialize(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "start_date": f"{self.start_date:%Y-%m-%d}",
            "end_date": f"{self.end_date:%Y-%m-%d}",
        }
        if self.buddy_period:
            data["buddy_period_start_date"] = f"{self.buddy_period[0]:%Y-%m-%d}"
            data["buddy_period_end_date"] = f"{self.buddy_period[1]:%Y-%m-%d}"
        data.update(
            {
                "availability": {},  # TODO
                "pgy_2_3_gap": self.pgy_2_3_gap,
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
