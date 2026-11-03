from pydantic import BaseModel


class GateInput(BaseModel):
    user_id: str
