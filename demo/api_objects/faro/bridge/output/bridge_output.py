from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Link(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str
    left_field: str
    right_field: str


class Read(BaseModel):
    """Bridge's internal read, retained as evidence for Shield."""
    model_config = ConfigDict(extra="forbid")
    source: str
    scope_ids: list[str]
    member_ids: list[str]
    group: str
    start: date | None
    end_exclusive: date | None
    expression: str
    link: Link | None = None


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    evidence_ids: list[int]


class Observation(BaseModel):
    status: Literal["ready", "ask", "not_supported", "incomplete"]
    question: str
    company_id: str
    reason: str | None = None
    read: Read | None = None
    source: str | None = None
    unit: str | None = None
    period: str | None = None
    data_version: str | None = None
    rows: list[dict[str, str | float | None]] = Field(default_factory=list)
    source_evidence: list[dict] = Field(default_factory=list)
    record_ids: list[str] = Field(default_factory=list)


class BridgeOutput(Observation):
    supporting: list[Observation] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    catalogue_version: str | None = None
