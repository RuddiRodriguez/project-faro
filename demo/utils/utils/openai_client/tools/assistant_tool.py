from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AssistantTool(ABC):

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        ...