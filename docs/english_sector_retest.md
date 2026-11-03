# English-only sector retest

Five questions were submitted through the real console after login. All ten APIs and the configured model were used. Application code and source data were not changed during this retest. The reference date was fixed to 2026-11-03, so “last month” means October. Each question used a fresh conversation, with a new data collection for the session.

| User / question | Expected values in executed reads | Time | Model calls |
|---|---|---:|---:|
| maria: Which berths had the most crane idle hours last month? | Pass | 57.5 s | 9 |
| sam: How many units did all our stores sell in October 2026? | Pass | 62.8 s | 9 |
| hospital_ops: Compare hospital bed occupancy in October 2026, highest first. | Pass | 67.3 s | 8 |
| sam: How many units did each store sell in October 2026? | Pass | 54.6 s | 8 |
| hotel_hq: How many hotels do we have? | Pass | 12.8 s | 4 |

All five answers were manually reviewed and were in English. Saved source documents exist and their content fingerprints match the versions returned with the answers. No model retry was needed, and none of these answers reused an application cache. The hotel check counted the three distinct active hotel records returned by the read, rather than requiring a separate numeric count row. These are one-run checks, not a broad reliability or speed benchmark.

## Remaining qualifications

- Maria: the berth totals match the records (S1 115 hours, N1 100, N2 86, S2 71). The answer still calls the equipment “cranes”, although the cited records do not explicitly establish that equipment category. The numeric check passes; this wording issue remains.
- Sam: the total is 1,050 and the store totals are East 1,000 / West 50. The store-by-store response explicitly notes that the source does not specify a unit; the total response does not include that qualification.
- Hospitals: all six occupancy percentages and their descending order match the source data: Central 95%, Lakeside 90%, Hillview 85%, Westhaven 80%, Riverside 75%, Meadow 65%.
- Hotels: the count is 3.

## Exact answers

### maria: Which berths had the most crane idle hours last month?

S1 had the most crane idle time in October 2026: 115 hours. The next highest were N1 (100 hours), N2 (86 hours), and S2 (71 hours).

### sam: How many units did all our stores sell in October 2026?

All stores recorded 1,050 units sold in October 2026 (East: 1,000; West: 50). October coverage is marked complete for both stores.

### hospital_ops: Compare hospital bed occupancy in October 2026, highest first.

1. Central Hospital — 95% occupancy (4,712 occupied / 4,960 available bed days).
2. Lakeside Hospital — 90% occupancy (6,138 / 6,820 bed days).
3. Hillview Hospital — 85% occupancy (2,635 / 3,100 bed days).
4. Westhaven Hospital — 80% occupancy (4,464 / 5,580 bed days).
5. Riverside Hospital — 75% occupancy (3,255 / 4,340 bed days).
6. Meadow Hospital — 65% occupancy (1,612 / 2,480 bed days).

### sam: How many units did each store sell in October 2026?

For October 2026, the recorded sold totals were East: 1,000 and West: 50; the source does not specify a unit.
Only supported findings are shown.

### hotel_hq: How many hotels do we have?

There are 3 active hotels as of 2026-11-03.

[Recorded results](validation/english_sector_retest.json)

Local console log: `tmp/english_sector_check_20261103_162741/console.txt`.
