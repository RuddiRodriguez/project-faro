from typing import Literal

from pydantic import BaseModel


class SignalOutput(BaseModel):
    initial_analysis: str | None = None
    reasoning: str | None = None
    action: Literal["Continue", "Ask", "Unsupported"]
    missing_choice: str | None = None
