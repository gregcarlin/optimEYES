from abc import ABC, abstractmethod
from datetime import date


class ProjectInfo(ABC):
    @abstractmethod
    def get_residents(self) -> list[str]:
        pass

    @abstractmethod
    def get_min_pgy(self) -> int:
        pass

    @abstractmethod
    def get_max_pgy(self) -> int:
        pass

    @abstractmethod
    def get_start(self) -> date:
        pass

    @abstractmethod
    def get_end(self) -> date:
        pass
