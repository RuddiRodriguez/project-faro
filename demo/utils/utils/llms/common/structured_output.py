from typing import Any, Dict

from pydantic import BaseModel, Field


class StructuredOutput(BaseModel):
    name: str = Field(min_length=1)
    json_schema: Dict[str, Any]
    strict: bool = True
    description: str | None = None

    def to_api_input(self) -> Dict[str, Any]:
        result = {
            "type": "json_schema",
            "name": self.name,
            "schema": self.json_schema,
            "strict": self.strict,
        }
        if self.description is not None:
            result["description"] = self.description
        return result
