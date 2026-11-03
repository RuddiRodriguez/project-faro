from pydantic import BaseModel


class PredictorInput(BaseModel):
    company_id: str
    query: str
    document_ids: list[str]
