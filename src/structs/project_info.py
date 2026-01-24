from abc import ABC, abstractmethod


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
