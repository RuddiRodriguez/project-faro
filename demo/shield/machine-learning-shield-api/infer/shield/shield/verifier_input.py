from api_objects.faro.bridge.input.bridge_input import BridgeInput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput


class VerifierInput(BridgeInput):
    evidence: BridgeOutput
