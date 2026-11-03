from pydantic import BaseModel, Field


class Passage(BaseModel):
    title: str
    text: str


class GuideInput(BaseModel):
    user_messages: list[str] = []
    question_text: str = Field(min_length=1)
    missing_choice: str = Field(min_length=1)
    passages: list[Passage]
    language: str | None = Field(default=None, description="Reply language, e.g. en or es.")
