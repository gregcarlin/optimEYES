from typing import Sequence
from abc import ABC, abstractmethod


class SummaryMetric(ABC):
    @abstractmethod
    def summary_metric_header(self) -> str:
        pass

    @abstractmethod
    def summary_metric(self, assignments: Sequence[Sequence[str]]) -> dict[str, str]:
        """
        Given a list of assignments (one entry for each day, each entry has
        list of residents assigned to that day), return a dict of resident ->
        summary value to display.
        """
        pass


class DetailMetric(ABC):
    @abstractmethod
    def detail_metric_header(self) -> str:
        pass

    @abstractmethod
    def detail_metric(self, assignments: Sequence[Sequence[str]]) -> list[str]:
        pass
