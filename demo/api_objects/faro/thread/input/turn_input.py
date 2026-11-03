from typing import Literal
from pydantic import BaseModel
from api_objects.faro.thread.input.thread_input import ThreadInput

Detail = Literal["task", "subjects", "scope", "period", "measure", "order", "conditions"]


class Change(BaseModel):
    model_config = {"extra": "forbid"}
    field: Detail
    value: str | None


class TurnInput(ThreadInput):
    proposed_changes: list[Change] = []
    current_request: dict[Detail, str]
