from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class IndexHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_reference: str
    score: float
    metadata: dict[str, Any]
