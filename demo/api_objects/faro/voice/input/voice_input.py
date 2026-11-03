from pydantic import BaseModel, Field, model_validator
from api_objects.faro.shield.output.shield_output import ShieldOutput


class VoiceInput(BaseModel):
    question: str
    verification: ShieldOutput
    names: list[str] = Field(default_factory=list)
    measure: str | None = None
    definition: str | None = None
    definition_source: str | None = None

    @model_validator(mode="after")
    def check_verified_facts(self):
        if self.verification.status == "verified" and self.verification.facts is None:
            raise ValueError("A verified answer requires Shield facts")
        return self
