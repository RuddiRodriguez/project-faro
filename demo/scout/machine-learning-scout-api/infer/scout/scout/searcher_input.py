from pydantic import BaseModel


class SearcherInput(BaseModel):
    company_id: str
    query: str
    document_ids: list[str]
