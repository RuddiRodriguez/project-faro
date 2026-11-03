from api_objects.faro.connector.output.connector_output import ConnectorOutput
from connector.source_reader_input import SourceReaderInput


class SourceReaderEndpoint:
    def __init__(self, source_reader):
        self.source_reader=source_reader

    def handle(self, request):
        result=self.source_reader.read(SourceReaderInput.model_validate(request,from_attributes=True))
        return ConnectorOutput.model_validate(result,from_attributes=True)
