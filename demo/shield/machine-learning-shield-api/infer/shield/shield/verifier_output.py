from typing import Literal

from pydantic import BaseModel
from api_objects.faro.bridge.output.bridge_output import BridgeOutput


class VerifierOutput(BaseModel):
    status: Literal["verified", "withheld"]
    reason: str | None = None
    facts: BridgeOutput | None = None
