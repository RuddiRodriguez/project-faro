from api_objects.faro.connector.output.connector_output import SourceItem
from pydantic import BaseModel


class SearchMatch(BaseModel):
    document_id: str
    source: str
    file_reference: str
    title: str
    text: str
    version: str
    score: float
    source_id: str = ""
    page: int | None = None
    start: int = 0
    end: int = 0


class ScoutOutput(BaseModel):
    query: str
    matches: list[SearchMatch]
    source_items: list[SourceItem] = []
