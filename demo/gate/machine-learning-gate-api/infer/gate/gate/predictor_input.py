from pydantic import BaseModel


class PredictorInput(BaseModel):
    user_id: str
