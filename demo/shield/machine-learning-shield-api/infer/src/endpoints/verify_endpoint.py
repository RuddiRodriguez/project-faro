from api_objects.faro.shield.input.shield_input import ShieldInput as ApiVerifierInput
from api_objects.faro.shield.output.shield_output import ShieldOutput as ApiVerifierOutput
from shield.verifier import Verifier
from shield.verifier_input import VerifierInput as LibVerifierInput


class VerifierEndpoint:
    def __init__(self, verifier: Verifier):
        self.verifier = verifier

    def handle(self, api_input: ApiVerifierInput) -> ApiVerifierOutput:
        request = LibVerifierInput.model_validate(api_input, from_attributes=True)
        result = self.verifier.verify(request)
        return ApiVerifierOutput.model_validate(result, from_attributes=True)
