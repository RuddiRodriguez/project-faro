import json
from dataclasses import dataclass

from ..assistant_tool import AssistantTool


@dataclass
class AssistantFunction(AssistantTool):
    name: str
    raw_arguments: str

    def __post_init__(self):
        try:
            replaced_new_lines_with_space = self.raw_arguments.replace('\\n', '_*escaped_new_line*_').replace('\n', ' ').replace('_*escaped_new_line*_', '\\n')
            self.parsed_arguments = json.loads(replaced_new_lines_with_space)
        except:
            self.parsed_arguments = None

    @property
    def is_valid(self) -> bool:
        return self.parsed_arguments is not None
