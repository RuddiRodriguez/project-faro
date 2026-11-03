from pydantic import BaseModel

class Definition(BaseModel):
    title: str
    text: str
    source: str


class PredictorInput(BaseModel):
    unclear_references: list[str] = []
    question: str
    matches: list[Definition]
    connected_sources: list[str] = []
    supported_tasks: list[str]
    groups: dict[str, list[str]] = {}
    permitted_scopes: list[str]
