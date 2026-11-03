from pydantic import BaseModel


class AccessCheckerInput(BaseModel):
    user_id: str
