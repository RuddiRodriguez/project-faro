from pydantic import BaseModel


class ScoutInput(BaseModel):
    company_id: str
    query: str
    document_ids: list[str]
    permitted_scope_ids: list[str] = []
