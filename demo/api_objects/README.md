# Faro API objects

Shared repository of Pydantic messages. Each service has its own API input and output models; callers import the definitions for the service they call. This directory is a separate local Git repository; no remote or submodules are configured yet.

## Library: first request and response

```python
from api_objects.faro.library.input.library_input import LibraryInput
from api_objects.faro.library.output.library_output import LibraryOutput

request = LibraryInput(
    company_id="harbor",
    permitted_terminal_ids=["harbor_north"],
)
```

Compass supplies company and permissions verified by Gate. These fields are not authorization by themselves and must not be trusted directly from a user.

LibraryOutput contains the company information, permitted terminals, relevant company documents, and agreements. Supported tasks are currently stored in a company document in the demo dataset. Operational activity and results are not part of this response.

Library will select the permitted information. These classes validate message structure only: they do not read data, filter access, approve documents, choose effective agreements, or start an API.

MongoDB `_id` is storage information, not part of these service messages. Dates accept ISO strings and serialize back to ISO strings through `model_dump(mode="json")`.

## Existing code style

Matches Japan's small BaseModel classes, typed fields, List imports, separate input/output files, and nested output models. References:

- `/Users/ruddigarcia/machine-learning-japan/japan/predictor_input.py`
- `/Users/ruddigarcia/machine-learning-japan/japan/predictor_output.py`
- `/Users/ruddigarcia/Projects/machine-learning-japan-api/api_objects/kali/japan/input/predict_input.py`

Japan's survey/media fields do not fit Library, so its model pattern is reused rather than those unrelated definitions. No custom base classes, validators, or legacy field aliases are added.

## Install in the shared environment

From the demo directory:

```sh
venv/bin/python -m pip install -e ./api_objects
venv/bin/python -m unittest discover -s api_objects/tests -v
```

## Per-service structure

Each of Compass, Gate, Library, Thread, Scout, Signal, Guide, Bridge, Shield and Voice has:

- API input: `faro/<service>/input/<service>_input.py`, class `<Service>Input`.
- API output: `faro/<service>/output/<service>_output.py`, class `<Service>Output`.
- Separate library input/output: `demo/<service>/machine-learning-<service>-api/infer/<service>/<service>/predictor_input.py` and `predictor_output.py`, classes `PredictorInput` and `PredictorOutput`.

API models describe messages exchanged between services. Library models describe inputs and outputs of the service's internal code. They are separate classes, not aliases or subclasses of one another.

Only Library's API fields are currently defined. All other API models and all library models are empty placeholders. Do not use them to validate real requests yet: an empty Pydantic model has no business fields. We will define each service's fields and API-to-library mapping when implementing it, following Japan's style.

The shared API-object repository is initialised. Service repositories, submodules, API routes, and service implementations are not created yet.
