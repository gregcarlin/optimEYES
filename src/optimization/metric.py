from typing import Sequence
from abc import ABC, abstractmethod

class SolutionMetric(ABC):
    @abstractmethod
    def solution_metric(self, assignments: Sequence[Sequence[str]]) -> dict[str, str]:
        """
        Given a list of assignments (one entry for each day, each entry has
        list of residents assigned to that day), return a dict of resident ->
        summary value to display.
        """
        pass
