from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class OrchestratorInput(BaseModel):
    conversation_id: UUID | None = None
    previous_answer_id: UUID | None = None
    user_id: str
    question: str
    language: str | None = None
    conversation: list[ConversationMessage] = Field(default_factory=list)
