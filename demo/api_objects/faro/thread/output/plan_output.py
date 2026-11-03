from typing import Literal
from pydantic import BaseModel, ConfigDict
from datetime import date


class Ranking(BaseModel):
    model_config = ConfigDict(extra="forbid")
    definition_id: str
    scope_ids: list[str]
    group: str
    member_ids: list[str]
    start: date
    end_exclusive: date
    order: Literal["highest", "lowest"]


class PlanOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ready", "ask", "unavailable", "unsupported"]
    selected_definition_id: str | None
    ranking: Ranking | None
    reason: str | None
