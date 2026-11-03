# Connected-source search improvements

Faro keeps the same service flow. Connector reads permitted files, Scout helps locate useful passages, Bridge reads the underlying evidence, and Shield checks the answer. The client does not prepare a glossary.

## What changed

- Connector now reads CSV and Parquet using the same small reader interface as the existing formats. CSV preserves text such as `001`; Parquet retains typed values. The same access checks, source fingerprints and document exports apply. Oversized reads are refused rather than sampled.
- Scout splits each PDF page separately into overlapping passages. Each match retains the connected source ID, page, exact character positions in extracted text and source version. Numbers and identifiers are preserved.
- Scout combines the existing local multilingual embedding search with word search. It merges results by passage reference. Search scores describe ordering, not answer confidence. The old minimum meaning-score cutoff no longer drops potentially useful hints.
- Index keys include the passage-format version, company, permitted items, document versions and embedding revision. Unchanged indexes remain reusable. No second cache was added.
- Compass passes Scout's passages to Bridge. Bridge keeps only hints matching its current permitted source IDs and versions. Hints cannot be cited as executed evidence: Bridge must read the source, and Shield repeats that read.
- Successful table-link checks are now visible to Bridge and Shield. The existing code already rejects missing keys, duplicate right-side keys and unmatched key sets. The new `link_check` reports those checks and the source row counts. Shield repeats the checks and rejects altered reports. This does not establish reporting-period coverage or business meaning.

The existing search library, shared model utilities, provider selection and execution restrictions were not replaced. The reused ideas were adapted into the current reader/search structure; no old application framework or company-specific tagging rules were brought in.

## Separate search experiment

Ten constructed, labelled questions cover English, Spanish, exact identifiers, terminal operations, healthcare, hotels, retail and other records. Expected source IDs and page locations are checked separately from answer wording.

| Search method | Expected source first | Expected source in first three |
|---|---:|---:|
| Previous meaning search and cutoff | 9/10 | 9/10 |
| Meaning search without cutoff | 10/10 | 10/10 |
| Combined meaning and word search | 10/10 | 10/10 |
| Combined search plus extra reranking model | 9/10 | 9/10 |

The measurable gain in this set comes from removing the cutoff: a Spanish question was previously discarded. These results do not demonstrate a separate accuracy gain from word search. The extra reranking model is available only in the evaluation script; it is not enabled in Faro because it reduced retrieval success here. These are small local evaluation cases, not a production accuracy claim.

Reproduce from the repository root:

    demo/venv/bin/python demo/scripts/evaluate_search.py --output tmp/search-evaluation.json

Use `--rerank` to run the extra-model comparison. That experiment needs sentence-transformers and downloads its public cross-encoder checkpoint. The normal service does not need it.

## Maria before and after

The console question is: “Which berths had the most crane idle hours last month?” Each run starts with Maria's login and a fresh data collection. The reference date is fixed to 2026-11-03. The source files and configured generation models are unchanged. The source-backed expected totals are S1 115 hours, N1 100, N2 86 and S2 71 for October.

Baseline commit: `2f177c6d001e7593f10576a3ee9e783b8dd0a9d3`. Each stage has three live runs. Full local console logs and saved turns are under `tmp/search_comparison/`. The reusable runner is `demo/scripts/compare_maria_search.py`; pass a new label to avoid overwriting a previous run.

The intermediate search-only changes still produced unnecessary refusals. They exposed a gap between the table-link checks performed in code and the evidence shown to the reviewing model. Those intermediate results are retained in the comparison, rather than omitted.

Model generation varies, provider-side prompt caching was not controlled, and this small sequential comparison cannot establish production speed or reliability. A quick refusal is not a performance improvement over a correct answer. Table-link evidence is now explicit, but the model can still choose an unsuitable read or decline a question it could answer.

## Observed console results

| Stage | Runs releasing expected berth totals | Response times (seconds) | Model calls |
|---|---:|---|---|
| Before | 2/3 | 69.5, 56.3, 26.2 | 10, 9, 5 |
| Intermediate search changes | 1/3 | 25.2, 67.9, 39.5 | 4, 7, 7 |
| Final changes | 3/3 | 62.0, 36.0, 45.2 | 8, 6, 7 |

These release counts refer to the expected numerical berth totals, not complete semantic or language correctness. The first final answer switched to Spanish despite an English question. It also qualified that the evidence did not explicitly identify the equipment as cranes. Another final answer used “crane” without that qualification. The unchanged source files name equipment IDs and idle time but do not explicitly establish that equipment category. This remains an answer-quality limitation; no data was added to hide it.

The final changes make already-executed link checks visible. They do not prove that every model decision is correct. A larger evaluation is needed before claiming general improvements in reliability, latency or cost.

## Validation and scope

- Complete: CSV/Parquet readers, overlapping page passages, combined search, source/version-aware hints to Bridge, and explicit existing link-check evidence.
- Complete: optional extra-model evaluation. Not enabled in the running service because the measured retrieval result was worse.
- Complete: 96 local tests checked, 84 passed and 12 opt-in tests skipped. This consists of the 95-test suite plus the added CSV/Parquet HTTP-to-Bridge test. No failing test remains.
- Complete: three baseline, three intermediate and three final real-model console runs of Maria's same question. The intermediate failures are retained.
- Remaining limitation: output-language consistency and unsupported equipment-category wording. Broad production accuracy and speed are not established by these small tests.

Tests include unchanged-index reuse, source changes, multilingual source retrieval, permission filtering, exact PDF page/character references, preserved CSV IDs, scoped document exports, oversized-read rejection, CSV/Parquet totals through the actual Connector API, and rejection of forged link-check evidence before model review.

[Recorded comparison](validation/search_improvements.json)

## Subsequent scope change: English only

After the comparison above, reply-language preferences and translation were removed. The demo now assumes English questions and source data, and requests English answers and follow-ups. The earlier results remain historical evidence; current search cases use English. The existing embedding weights are unchanged.
