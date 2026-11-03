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


class ScoutOutput(BaseModel):
    query: str
    matches: list[SearchMatch]
    source_items: list[SourceItem] = []
