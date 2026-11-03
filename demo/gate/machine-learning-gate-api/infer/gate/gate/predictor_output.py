from typing import List

from pydantic import BaseModel


class PredictorOutput(BaseModel):
    user_id: str
    company_id: str
    permitted_scope_ids: List[str]
    permission_version: str
