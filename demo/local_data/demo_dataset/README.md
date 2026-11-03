# Faro demo data

Fictional data for developing and testing Faro. JSON files represent MongoDB-style collections; no MongoDB server is running.

Each collection is a JSON array of documents. Every document has a unique string `_id`. Related operational documents use `company_id`, `scope_id`, `asset_id`, and other explicit references. Dates use ISO strings for now; no BSON or ObjectId conversion is required to read these files.

## Companies and people

- Harbor Operations, Netherlands: Maria and Luis can see both terminals; Ana only North. Noah has no terminal permissions. A former user is disabled.
- Pacific Cargo, California: Maya can see both terminals. Its agreed moves-per-hour indicator uses scheduled hours.
- Strait Logistics, Singapore: Chen can see North only. Its indicator uses operating hours.

The three port companies have a North Terminal, South Terminal, and cranes named C01 and C02. IDs remain unique. This deliberately tests whether names are resolved within the correct company and terminal.

Retail, hospital and hotel examples use the same services. See [four sectors and test questions](../sector_examples/README.md).

## Collections

| JSON file | What it contains |
|---|---|
| companies.json | Company identity, time zone, information versions |
| users.json | User identity, company, permissions, active/disabled status |
| terminals.json | Company terminals and name aliases |
| assets.json | Crane identifiers, display names, active dates |
| agreements.json | Approved performance targets, indicator references, effective dates, reporting rules |
| documents.json | Searchable company meanings and supported questions |
| activity.json | Daily crane activity for September and October 2026 |
| coverage.json | Expected and received days per crane and month |
| conversations.json | Maria's question and clarification replies |
| data_cache.json | Saved company comparison, with period and source version |
| ai_cache.json | Saved classification inputs, decision, and version labels |
| cases.json | Questions, users, scenario references, and expected behavior |
| scenarios.json | Separate changes used to test missing data, failures, changed permissions, and other cases |
| expected_answers.json | Reference October rankings derived from the base activity |
| manifest.json | Dataset counts, date used by default, and scope |

`client_formats/` contains JSON documents shaped differently for each client. One uses hours, another scheduled minutes, another operating minutes. These files are input examples for later client connections; they are not additional activity to append to the shared activity collection. They cover the productivity fields needed for that example, not every possible indicator.

## Start with Maria

1. Use `clear_ranking` in cases.json and the untouched base collections.
2. Read her company and permissions from users.json.
3. Find the Harbor definition in documents.json.
4. Use Harbor North's October activity.
5. Compare the result with `harbor_north` in expected_answers.json.
6. Try `clarification_loop` to reach the same question through follow-ups.
7. Try `same_data_luis`: Luis asks the same question while Maria is on holiday.

Default clock: 1 November 2026, 12:00 UTC. A case may provide a different clock; the time-zone case deliberately does.

## Cases covered

- Clear questions; missing terminal, indicator, period, or ambiguous crane name.
- Explanations from documents versus rankings from operational records.
- Different companies with identical terminal/crane names and different KPI meanings.
- Agreement targets, expired/draft agreements, and targets changing mid-month.
- Restricted access, disabled users, revoked permissions, and another user's conversation.
- Unsupported payroll and unsupported fault diagnosis.
- Missing days/cranes, null/negative/zero hours, duplicate records, corrections, deletions, and ties.
- Missing/conflicting meanings and untrusted document instructions.
- Time zones and unavailable periods.
- Company-specific data reuse; changed month, company, reply, or model instructions.
- Search failure, data timeout, incorrect answer values, and unsupported causal claims.

## How scenarios work

Always start with a fresh copy of the base data. Apply only the scenario named by the case. Scenarios describe the intended changes; the scenario runner will be implemented later.

An appended revision inherits the original record fields and changes the listed fields. Latest revision replaces earlier revisions; a deleted latest revision removes the record from active results. Recheck coverage after deletion.

The changed-target scenario replaces the old target from its new effective date. It does not silently create overlapping valid targets. If the company has no rule for a month with two targets, the expected response asks how the comparison should be presented.

A zero-hour day with zero moves does not automatically invalidate a monthly ratio: use the agreed monthly totals. An entire period with zero denominator cannot produce a ratio. Unknown coverage is not proof of no activity.

Cache entries are example documents, not evidence that caching already works. `demo-model-version` is a fixture label, not an actual model. Document source paths are logical references carried by the fixture; the searchable text is in documents.json.

## Expected outcomes

`ANSWER`, `ASK`, `DENY`, `UNSUPPORTED`, `WITHHOLD`, and `ERROR` describe test expectations. They are not all Decision API classifications and do not prescribe the future API format.

Rankings include exact integer totals and ratios rounded to four decimal places. Use unrounded totals for ordering and target comparisons. Reference answers are derived data, not observed outputs from Faro services.

This fixture set is for terminal operations. It tests multiple client layouts; it does not yet demonstrate a different sector. Further cases can be added as each service is built.

## Recreate

From the demo directory:

```sh
venv/bin/python scripts/create_demo_data.py
```

This overwrites generated fixture JSON files. No service code, model calls, or database setup is required.
