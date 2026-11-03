# Release review — 3 November 2026

The current connected-source update is documented in [Connected-source design update](connected_sources_update.md). The sections below describe the earlier release, including its now-removed prepared-data contract.

## Work included

- Created one root repository containing the service libraries, APIs, shared API objects, fixtures, tests and proposal artifacts. The previously initialized but uncommitted api_objects Git metadata was preserved outside the project in ../assesment-backups/pre-publish/api_objects.git so its files can be tracked normally.
- Renamed each service class, implementation file, input/output file, endpoint and caller to its actual responsibility. Original shared model utilities and knowledge search keep their source names.
- Removed obsolete Thread ranking and turn-edit endpoints, prompts and request objects, the unused fixed-field follow-up changes, and an unused ranking-definition field. Current free-form rewriting and Bridge evidence reads remain.
- Removed 53 empty scaffold directories. Retained Python package initializers and useful tests.
- Reorganized model prompts around the shared role, objective, initial analysis, reasoning and response sections. User input has named templates. Pydantic schemas remain beside the prompts.
- Saved brief initial_analysis and reasoning summaries in model_calls.explanations_json and conversation exports. Signal returns those as choices in the same Decision API call; no separate explanatory generation call was added.
- Added generality and stress tests with six schema vocabularies, including recycling and unfamiliar column names, plus source-access, oversized-read, worker-boundary and summary-persistence checks.
- Corrected older tests whose two-location assumption no longer matched multi-sector data. Removed tests for the deleted ranking planner. Live model tests now require explicit opt-in; local tests do not silently make paid calls.
- Kept three-source attachments and the expanded hospital fixtures. Updated README, SQL field origins and both PDFs; the PDF builder is now self-contained under docs/pdf.
- Kept Shield's rewritten findings in the question's language through its prompt, without a language detector.
- Removed unused application imports. Reusable copied dependency code was left intact.

## Boundaries that remain

Faro is not proven to work with any arbitrary client. It has reusable question services and three native file readers. Exact-key relationships, whole-file permissions, bounded local reads and the prepared JSON data contract remain explicit limits. Production sign-in, remote connectors, OCR, row-level permissions and a non-macOS expression sandbox remain future work.

All tests use fictional company records. Local stress tests prove specific code behavior; selected live-model tests prove those observed conversations. They do not establish production security, universal correctness or client adoption.

Credentials, the local environment, weights, indexes, runtime conversations, generated source-document copies and temporary renderings are excluded from Git. The maintained PDFs and their source are included. Root PowerPoint files are historical drafts.

## Reference cleanup

Removed internal-project names, private source paths and private-repository comparison tooling from the current distributable files. Retained local utility integrity tests. Both PDFs now reference only Faro code. Search package imports were renamed consistently and the shared environment was refreshed. Historical Git commits remain unchanged.
