class Resident:
    def __init__(
        self, name: str, pgy: int, availability: list[int], coverage: dict[int, str]
    ) -> None:
        self.name = name
        self.pgy = pgy
        self.availability = availability
        self.coverage = coverage
