# Faro API objects

Each service has separate Pydantic request and response classes under faro/<service>/input and faro/<service>/output. These classes are shared by the calling service and the receiving API.

Library-level inputs and outputs stay inside each service library. Endpoints explicitly convert API fields to library fields and back.

Install from demo/ in the shared environment:

    python -m pip install -e ./api_objects

Run the contract tests:

    python -m unittest discover -s api_objects/tests -v
