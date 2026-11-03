from pydantic import BaseModel


class SourceItem(BaseModel):
    id: str
    kind: str
    location: str
    fields: list[str]
    scope_ids: list[str]
    version: str


class ConnectorOutput(BaseModel):
    items: list[SourceItem]
    rows: list[dict] = []
    references: list[str] = []
    document: dict | None = None
