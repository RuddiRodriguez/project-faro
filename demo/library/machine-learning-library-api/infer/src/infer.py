import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from api_objects.faro.library.input.library_input import LibraryInput
from api_objects.faro.library.output.library_output import LibraryOutput
from library.information_reader import LibraryRequestError, InformationReader
from library_api.endpoints.read_endpoint import InformationReaderEndpoint


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "local_data/demo_dataset"


def create_app(data_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Library — reads saved company information")
    endpoint = InformationReaderEndpoint(InformationReader(data_path or Path(os.getenv("FARO_DATA_PATH", DEFAULT_DATA_PATH))))

    @app.post("/v1/company-information", response_model=LibraryOutput)
    def read_company_information(request: LibraryInput) -> LibraryOutput:
        try:
            return endpoint.handle(request)
        except LibraryRequestError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    return app


app = create_app()
