# Connected-source design update — 3 November 2026

The client grants access to data and asks questions. There is no prepared glossary, approved-indicator collection or supported-task list in the running flow.

## What changed

- Removed Library's service, endpoint, client, API objects and installation entries. The console starts ten APIs.
- Gate remains the authority for the selected user's company and permissions. Compass calls Connector directly to list permitted sources. Its response now contains `sources`, replacing `company_information`.
- Connector owns source locations and grants. Existing demo records are exposed as JSON files alongside SQLite, Excel and PDF. JSON grants can name an access-scope field; filtering happens before records or document copies leave Connector. This setting controls access, not business meaning.
- Removed Bridge's prepared-data reader and its dependencies on company definitions, agreements and supported tasks. Bridge and Shield both use Connector. They inspect source fields and records, and use existing source notes when relevant; they do not require clients to author those notes.
- Scout builds E5/FAISS indexes from connected field names and PDF passages. Index keys include company, access, source versions and model version. The first search prepares an index; later searches reuse it. The knowledge-search request/result shape remains unchanged.
- Classification no longer receives a supported-task list. Guide receives relevant source passages, not a prepared collection of company definitions.
- Existing rich sector records remain intact. The demo read limit is now 1,000 rows so the hospital source fits; oversized reads still fail instead of returning a sample.
- Bridge keeps six read attempts and now has a final model decision after the last read. Its prompt distinguishes a missing user choice from permission to continue reading: permitted reads are already authorized.
- Updated both 19-page PDFs and service documentation. The reference edition keeps code links beside their sections. No changes were made to the user's existing PowerPoint edit.

## Evidence

- The default local suites pass; see validation.md for the final count. Tests for the removed Library and prepared-data contract were replaced with connected-source contracts, native-source access, replay and changed-source checks. These are not the same test population as the previous release.
- Three live HTTP tests pass for a new client whose folder contains only accounts, connection settings and a SQLite file: total booked nights (9), denied/empty access, and clarification followed by per-property totals (7 and 2). No company metadata, glossary, agreements or task list exists in that test folder.
- The four-sector console test passes: Maria's berth question returns S1 at 115 hours and all three original source documents; retail returns 1,050 sold units; hospital occupancy returns the six expected values; hotel inventory returns three active hotels.
- Maria's explicit clarification console test passes after the read-budget correction: Ask, then verified, with North Terminal cranes tied at 62 downtime hours in October. Thread preserved the question and the saved model-call summaries are present.
- Local E5 tests cover English and Spanish search, unchanged-index reuse, changed-version invalidation and the AWS-style result format.
- Both PDFs were rendered and visually checked. All 52 source links in the reference copy resolve to existing repository files.

## Failures retained in the record

The first standalone berth attempt exhausted its model budget and withheld the answer; subsequent berth runs passed. An earlier clarification run returned no usable structured response. A fresh run then asked for permission to finish reading. The generic prompt and final-decision correction addresses that latter behavior, and its exact console test passed afterward. These observations do not establish that model output is deterministic. No guardrail was relaxed to force a result.

This remains a local demo. Production identity, remote source drivers, broader document extraction, production authorization and background indexing remain work to build. The client-facing requirement does not mean every possible source can already be read.
