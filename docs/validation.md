# Validation — 3 November 2026

## Connected-source update

See [the change and test record](connected_sources_update.md) for the current ten-service flow. The default local run discovered 89 tests: 77 passed and 12 opt-in tests were skipped, with no failed suites. Separately, the three new-client HTTP checks, four-sector console check, and Maria clarification check passed. The records below describe the earlier release and are retained as historical evidence.

## Earlier release

This review distinguishes local code tests from conversations using the configured models. All business records are fictional fixtures.

## Local checks

The default run discovered 130 tests: 95 passed and 35 opt-in tests were skipped. No suite failed.

The complete default test runner covers every service test directory, shared API objects, utilities and cross-service tests. Paid-model tests require an explicit opt-in; they are not counted as local passes.

New stress tests run the same connector and worker against six different field vocabularies: terminal operations, retail, hospitals, hotels, recycling and arbitrary names. They also test company isolation, unknown fields, oversized sources, unsafe expressions and invalid numeric results. This supports reuse across these tested structures, not a claim that every database or sector is supported.

Local integrity tests check the included utility files against their recorded hashes. Ruff's unused-import, duplicate-name and undefined-name checks passed for application code; copied dependency code was excluded from that cleanup.

## Real model and console checks

Both selected live console tests passed (136.3 seconds together), covering six submitted messages across four sectors. The earlier startup failure caused by an import cleanup was corrected and the complete selected console checks were rerun. A local import check now covers that regression. A later run exposed mixed-language wording in Shield's narrower findings; its prompt was clarified and both live tests passed again with English answers to these English questions. Shield's 13 local tests also passed after that change.

The selected console tests start all eleven APIs, log in, ask questions and inspect the saved company data collection. They cover:

- Maria's berth question, using SQLite, Excel and PDF together.
- A retail units total.
- A six-hospital occupancy comparison.
- A hotel count.
- A clarification followed by Maria's choice of downtime, North Terminal and October 2026.

Saved responses check company identity, expected values, document references and short model explanations. The saved evidence files beside this document contain the observed answers. They are specific test results, not a guarantee that a model will always choose the same analysis.

## Documentation and publishing checks

Both maintained proposals were rebuilt from the committed PDF source. All 19 pages in each copy were visually inspected. The delivery copy has no private project links; the reference copy keeps Faro implementation links beside the relevant sections. Repository link targets exist locally.

Credentials, environments, model weights, indexes and runtime collections are excluded from version control. Credential-pattern scans of staged files and the initial commit found no matches. No empty source directories remained after cleanup.

## What was not established

The wider opt-in live conversation suite was not run in this release review. A fresh-machine installation and the public model-download path were not exercised; the live runs used the existing local environment and weights. Production authentication, remote sources, scanned PDFs, row-level permissions, non-macOS execution and universal client compatibility remain outside the tested demo.

The model runtime can print a macOS semaphore-cleanup warning during shutdown. This did not prevent the observed console runs from completing.

## Reference cleanup

Internal-project references were removed from current source files, documentation, PDF references and historical slide notes. The search and embedding packages now have neutral names. The full local suite passed again (95 passed, 35 paid-model tests skipped), and a login-and-exit console check started all eleven APIs. The model-backed conversations above belong to the preceding validation run; they were not rerun for this naming-only change. Provider model IDs and country names remain unchanged. Earlier Git commits were not rewritten.
