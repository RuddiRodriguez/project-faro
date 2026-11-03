from typing import List

from pydantic import BaseModel


class LibraryInput(BaseModel):
    company_id: str
    permitted_scope_ids: List[str]
