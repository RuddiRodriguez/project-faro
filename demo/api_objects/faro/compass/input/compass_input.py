from uuid import UUID
from pydantic import BaseModel, Field

from api_objects.faro.thread.input.thread_input import ConversationMessage


class CompassInput(BaseModel):
    conversation_id: UUID | None = None
    previous_answer_id: UUID | None = None
    user_id: str
    question: str
    language: str | None = None
    conversation: list[ConversationMessage] = Field(default_factory=list)
