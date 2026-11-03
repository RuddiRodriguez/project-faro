from pydantic import BaseModel


class SearchMatch(BaseModel):
    document_id: str
    source: str
    file_reference: str
    title: str
    text: str
    version: str
    score: float


class SearcherOutput(BaseModel):
    query: str
    matches: list[SearchMatch]
