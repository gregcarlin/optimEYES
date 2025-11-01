class Resident:
    def __init__(
        self, name: str, pgy: int, availability: list[int], va: list[int], coverage: dict[int, str]
    ) -> None:
        self.name = name
        self.pgy = pgy
        self.availability = availability
        self.va = va
        self.coverage = coverage
