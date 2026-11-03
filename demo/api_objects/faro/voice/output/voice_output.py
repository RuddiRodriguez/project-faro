from typing import Literal
from pydantic import BaseModel


class Document(BaseModel):
    name: str
    uri: str
    version: str
    references: list[str] = []


class VoiceOutput(BaseModel):
    status: Literal["verified", "withheld"]
    text: str
    definition: str | None = None
    documents: list[Document] = []
    sources: list[str]
    mode: Literal["ai", "direct", "fallback"]
