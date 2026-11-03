from typing import List

from pydantic import BaseModel


class InformationReaderInput(BaseModel):
    company_id: str
    permitted_scope_ids: List[str]
