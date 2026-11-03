from typing import Literal

from pydantic import Field
from ..openai_consts import Role
from ..conversation.message import Message


class SystemMessage(Message):
    role: Literal[Role.SYSTEM] = Field(default=Role.SYSTEM, frozen=True)
    content: str
