from dataclasses import dataclass
from typing import List, Optional

from .token_usage import TokenUsage

from ..conversation.assistant_message import AssistantMessage
from ..conversation.conversation import Conversation
from ..conversation.decisions_conversation import DecisionsConversation
from ..tools.assistant_tool import AssistantTool


@dataclass(frozen=True)
class PredictOutput:
    input_conversation: Conversation | DecisionsConversation
    assistant_message: Optional[AssistantMessage]
    assistant_tools: Optional[List[AssistantTool]]
    finish_reason: Optional[str]
    token_usage: Optional[TokenUsage]
    reasoning : Optional[str] = None
    decisions_response: Optional[dict] = None
    
    def _is_assistant_output_valid(self) -> bool:
        return (self.assistant_message is not None) or \
               (self.assistant_tools is not None and all(assistant_tool is not None and assistant_tool.is_valid for assistant_tool in self.assistant_tools))

    def _is_decisions_output_valid(self) -> bool:
        if self.decisions_response is None:
            return False
        answers = self.decisions_response.get("answers", [])
        names = [answer["name"] for answer in answers]
        expected_names = [question["name"] for question in self.input_conversation.questions]
        return bool(answers) and len(names) == len(set(names)) and set(names) == set(expected_names)

    @property
    def is_success(self) -> bool:
        if isinstance(self.input_conversation, DecisionsConversation):
            return self._is_decisions_output_valid()
        return (self.finish_reason is not None) and self._is_assistant_output_valid()
