# Try the same question flow in four sectors

These are fictional October 2026 examples. No data belongs to an actual hotel chain or hospital. The demo clock is November 1. Start the services as described in the Compass README. Send a POST to /v1/questions with user_id and question:

| User | Example question | Expected result from the prepared records |
|---|---|---|
| maria | Which cranes at North Terminal had the most downtime last month? | C01 and C02 tie at 62 hours. |
| sam | Which stores had the highest return rate in October 2026? | West 10%, East 2%. |
| hospital_ops | Rank all my hospitals by highest average outpatient waiting time in October 2026. | Hillview 45 minutes per visit, Riverside 30. Only aggregated counts and minutes are stored. |
| hotel_hq | Rank all my hotels worldwide by lowest occupancy rate in October 2026. | Tokyo Bay, Japan 70%; Madrid Central, Spain 80%; Mexico City Plaza, Mexico 90%. |
| madrid_manager | Show the October 2026 occupancy rate for Madrid Central, highest first. | Madrid Central 80%. Asking for Tokyo Bay must not return its figures or substitute Madrid. |

A company file defines its locations, users, approved measure, source fields and daily demo values. Company meanings never come from a hotel name or a wording rule in a predictor. Headquarters can see its chain's configured properties; it cannot see another company's data.

To rebuild the records from the demo folder, run `venv/bin/python scripts/create_demo_data.py`. Then rebuild the local search indexes with `HF_HUB_OFFLINE=1 venv/bin/python -c 'from scout.knowledge_index import build_indexes; build_indexes()'` and restart the services.

The prepared format currently supports sums and ratios over periods with checked daily coverage. This example uses one full month. Source systems must first supply data in that format.
