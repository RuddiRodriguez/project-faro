import json
from pathlib import Path

from gate.predictor_input import PredictorInput
from gate.predictor_output import PredictorOutput


class Predictor:
    def __init__(self, data_path: Path):
        self.data_path = Path(data_path)

    def predict(self, predictor_input: PredictorInput) -> PredictorOutput:
        users = json.loads((self.data_path / "users.json").read_text())
        user = next((item for item in users
                     if item["user_id"].lower() == predictor_input.user_id.lower()), None)
        if user is None or user["status"] != "active":
            raise PermissionError("User not found or account is disabled")

        return PredictorOutput(user_id=user["user_id"],
                               company_id=user["company_id"],
                               permitted_scope_ids=user["scope_ids"],
                               permission_version=user["permission_version"])
