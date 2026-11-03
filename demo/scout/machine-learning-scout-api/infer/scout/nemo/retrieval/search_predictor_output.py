from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from nemo.retrieval.index_hit import IndexHit


class SearchPredictorOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    hits: list[IndexHit] = []
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        return self.error_message is None
