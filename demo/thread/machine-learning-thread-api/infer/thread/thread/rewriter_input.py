from typing import List, Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class RewriterInput(BaseModel):
    question: str
    conversation: List[ConversationMessage] = Field(default_factory=list)
