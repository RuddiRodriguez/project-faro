from typing import Literal
from pydantic import BaseModel


class ConnectorInput(BaseModel):
    company_id: str
    permitted_scope_ids: list[str]
    action: Literal["discover", "inspect", "read"]
    item: str | None = None
    fields: list[str] = []
