from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchFilterOperator(StrEnum):
    EQUALS = "Equals"
    GREATER_THAN = "GreaterThan"
    GREATER_THAN_OR_EQUALS = "GreaterThanOrEquals"
    IN = "In"
    LESS_THAN = "LessThan"
    LESS_THAN_OR_EQUALS = "LessThanOrEquals"
    LIST_CONTAINS = "ListContains"
    NOT_EQUALS = "NotEquals"
    NOT_IN = "NotIn"
    STARTS_WITH = "StartsWith"
    STRING_CONTAINS = "StringContains"

    @property
    def bedrock_name(self) -> str:
        return self.value[0].lower() + self.value[1:]


class SearchFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operator: str
    key: str
    value: Any


class SearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_base_id: str
    query: str
    top_k: int = 10
    minimum_relevance_score: float | None = None
    scope_filterable_keys: list[str]
    filters: list[SearchFilter] = Field(default_factory=list)
