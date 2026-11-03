from pydantic import Field
from typing import Literal
from ..openai_consts import Role
from ..conversation.message import Message


class AssistantMessage(Message):
    role: Literal[Role.ASSISTANT] = Field(default=Role.ASSISTANT, frozen=True)
    content: str
