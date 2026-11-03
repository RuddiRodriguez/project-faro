from datetime import date
from pydantic import BaseModel


class PlanInput(BaseModel):
    question: str
    selected_measure: str | None = None
    reference_date: date
    supported_tasks: list[str]
    definitions: dict[str, str]
    ranking_definition_ids: list[str]
    documented_choices: dict[str, str]
    scopes: dict[str, str]
    groups: dict[str, list[str]]
