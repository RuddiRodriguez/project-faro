from typing import List

from pydantic import BaseModel


class GateOutput(BaseModel):
    user_id: str
    company_id: str
    permitted_scope_ids: List[str]
    permission_version: str
