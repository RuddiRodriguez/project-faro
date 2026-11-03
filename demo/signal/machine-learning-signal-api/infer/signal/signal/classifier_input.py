from pydantic import BaseModel

class Passage(BaseModel):
    title: str
    text: str
    source: str


class ClassifierInput(BaseModel):
    unclear_references: list[str] = []
    question: str
    matches: list[Passage]
    connected_sources: list[str] = []
    permitted_scopes: list[str]
