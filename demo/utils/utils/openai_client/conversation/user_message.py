from typing import Literal

from pydantic import Field
from ..openai_consts import Role
from ..conversation.message import Message


class UserMessage(Message):
    role: Literal[Role.USER] = Field(default=Role.USER, frozen=True)
