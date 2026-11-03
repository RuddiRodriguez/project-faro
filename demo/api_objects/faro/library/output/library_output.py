from datetime import date
from typing import List

from pydantic import BaseModel


class CompanyInfo(BaseModel):
    company_id: str
    name: str
    timezone: str
    data_version: str
    definition_version: str


class ScopeInfo(BaseModel):
    company_id: str
    scope_id: str
    name: str
    aliases: List[str]


class CompanyDocument(BaseModel):
    document_id: str
    company_id: str
    scope_ids: List[str]
    title: str
    text: str
    status: str
    version: str
    source: str
    valid_from: date | None = None


class Agreement(BaseModel):
    agreement_id: str
    company_id: str
    scope_id: str
    title: str
    status: str
    valid_from: date
    valid_until_exclusive: date
    definition_id: str
    target: float
    target_unit: str
    comparison: str
    period_rule: str
    coverage_rule: str
    zero_hours_rule: str
    tie_rule: str
    owner_role: str
    version: str


class LibraryOutput(BaseModel):
    company: CompanyInfo
    scopes: List[ScopeInfo]
    documents: List[CompanyDocument]
    supported_tasks: list[str]
    groups: dict[str, list[str]]
    reference_date: date
    agreements: List[Agreement]
