from pydantic import BaseModel, ConfigDict


class LoggerMetadata(BaseModel):
    parent_request_uuid: str | None = None
    sample_id: int | None = None

    model_config = ConfigDict(frozen=True, extra="forbid")
