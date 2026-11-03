from pydantic import BaseModel, Field


class Definition(BaseModel):
    title: str
    text: str


class GeneratorInput(BaseModel):
    user_messages: list[str] = []
    question_text: str = Field(min_length=1)
    missing_choice: str = Field(min_length=1)
    definitions: list[Definition]
    language: str | None = Field(default=None, description="Reply language, e.g. en or es.")
