from typing import Any

from pydantic import BaseModel


class  Embedding(BaseModel):
    id: Any
    embedding: Any # This is a torch.Tensor, but Pydantic doesn't allow for non-atomic types as part of its specifications
