from typing import Literal

from pydantic import BaseModel


class SignalOutput(BaseModel):
    action: Literal["Continue", "Ask", "Unsupported"]
    missing_choice: str | None = None
