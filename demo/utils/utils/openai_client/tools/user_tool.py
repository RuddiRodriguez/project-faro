from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing_extensions import Literal


@dataclass(kw_only=True)
class UserTool(ABC):
    tool_type: Literal["function", "web_search"]

    TYPE_KEY_NAME = "type"

    @abstractmethod
    def to_api_input(self):
        ...
