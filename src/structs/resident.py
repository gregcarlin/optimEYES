from typing import Any, override


class Resident:
    def __init__(
        self,
        name: str,
        pgy: int,
        availability: list[int],
        va: list[int],
        coverage: dict[int, str],
    ) -> None:
        self.name = name
        self.pgy = pgy
        self.availability = availability
        self.va = va
        self.coverage = coverage

    def serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pgy": self.pgy,
            "schedule": self.availability,
            "va": self.va,
            "coverage": self.coverage,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> "Resident":
        return Resident(
            data["name"],
            data["pgy"],
            data["schedule"],
            data["va"],
            data["coverage"],
        )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Resident):
            return False
        return (
            self.name == other.name
            and self.pgy == other.pgy
            and self.availability == other.availability
            and self.va == other.va
            and self.coverage == other.coverage
        )

    @override
    def __hash__(self) -> int:
        return hash(self.name)
