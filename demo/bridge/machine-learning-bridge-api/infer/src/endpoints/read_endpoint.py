from api_objects.faro.bridge.input.bridge_input import BridgeInput as ApiReaderInput
from api_objects.faro.bridge.output.bridge_output import BridgeOutput as ApiReaderOutput
from bridge.reader import Reader
from bridge.reader_input import ReaderInput as LibReaderInput


class ReaderEndpoint:
    def __init__(self, reader: Reader):
        self.reader = reader

    def handle(self, api_input: ApiReaderInput) -> ApiReaderOutput:
        request = LibReaderInput.model_validate(api_input, from_attributes=True)
        result = self.reader.read(request)
        return ApiReaderOutput.model_validate(result, from_attributes=True)
