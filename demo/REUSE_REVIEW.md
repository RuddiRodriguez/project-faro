# What Faro reuses

Faro adapts existing code shapes, not an existing complete analytics product.

| Area | Existing project | Kept / adapted |
|---|---|---|
| API and library separation | Japan API | Separate Pydantic inputs and outputs; thin endpoint conversion; service-specific method names. |
| Compass | AI2Analytics forwarding | Calls the next service over HTTP. The orchestration and owned conversation collection are Faro code. |
| Thread | Luna rewriting, Japan build/call/parse | Rewrites relevant user replies through shared utils. No separate ranking planner remains. |
| Scout | Nemo retrieval, Luna E5 and FAISS | Nemo request/result method and retrieval classes retained. Local company indexes replace AWS. |
| Signal | Semantica Decision API, Japan classification | Original classifier call/error structure. Three choices in one call record action, assessment and reason. |
| Guide | Japan follow-up generator | Separate generator input/output, build conversation, call shared utils, parse structured response. |
| Prompts | Japan sufficiency and Gambit AI attributes | Role, objective, initial analysis, final reasoning, response; named USER_MESSAGE placeholders and Pydantic schemas. |
| Shared utilities | Original utils | StructuredOutput, conversation and prediction wrappers remain. Three-attempt retry and turn-level call recording are explicit demo adaptations. |
| Bridge / Shield | Existing Faro pandas path | General permitted reads and independent replay. Native connectors, source copies, key checks and evidence review are Faro additions. |
| Voice | Japan generation, Luna grounded answer | Presents checked findings directly; structured wording is used only when needed. |
| Connector | Existing factory/dispatch and forwarding patterns | A reader registry chooses SQLite, Excel or text PDF. No business field mapping in the readers. |

The original private projects are not required to run this repository. Their source checks are an opt-in developer audit. The portable unit suite verifies copied utility-file hashes. The private proposal retains original project references beside the relevant sections.

## Where the generality stops

The shared JSON reader requires prepared inventory and daily activity records. This is one data contract, not a universal company model. Native connector readers preserve each source's own names and need no hospital/crane/store keywords. Supported relationships are exact-key joins; incomplete or ambiguous links stop. OCR, remote-source readers and arbitrary time-based relationships are not implemented.

Source access is configured per file. A whole file must be permitted before a snapshot is returned. Legacy multi-company JSON data is exported only as the selected permitted records.

## Verify reuse

From demo/:

    python scripts/check_reused_sources.py
    FARO_CHECK_ORIGINAL_REPOS=1 python -m unittest discover -s utils/tests -v

Those commands require the original local repositories. Normal tests and console use do not.
