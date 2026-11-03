from pydantic import BaseModel


class BridgeInput(BaseModel):
    question: str
    company_id: str
    permitted_scope_ids: list[str]
    definition_ids: list[str]
