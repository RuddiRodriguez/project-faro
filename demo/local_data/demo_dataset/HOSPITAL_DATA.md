# Cedar hospital demo data

All information is fictional, deterministic operational test data. No patient records are included.

Sign in as `hospital_ops` for all six hospitals, or `riverside_manager` for Riverside only. Restart the console after regenerating data so it loads the refreshed search index.

## Available information

Six hospitals: Riverside (Rotterdam), Hillview (Utrecht), Lakeside (Amsterdam), Westhaven (The Hague), Meadow (Eindhoven), Central (Groningen).

Daily records run from 1 July through 31 October 2026. They contain outpatient visits and waiting minutes, emergency visits and waiting minutes, available and occupied bed-days, admissions, discharges, scheduled appointments and cancellations. The hospital register also contains city and staffed-bed capacity.

The ten company documents explain the eight indicators, supported questions and reporting coverage. Monthly coverage records state what is complete. Counts describe activity, not unique people. There is no evidence for medical advice, patient details or explanations of causes.

## Questions to try

- How many hospitals do we have?
- Compare hospital bed occupancy in October 2026, highest first.
- Which hospitals had the longest outpatient waiting time in October 2026?
- How many admissions did each hospital record in October 2026?
- Compare outpatient waiting time in July and October 2026.
- Which hospital had the highest appointment cancellation rate in October 2026?
- How many emergency visits were recorded during 19–25 October 2026?
- Compare outpatient waiting time across all hospitals in September 2026.

The final question should disclose the Westhaven coverage gap, not silently omit it.

## Known checks

October outpatient waiting averages: Central 50 minutes, Hillview 45, Westhaven 38, Riverside 30, Lakeside 25, Meadow 20.

October occupancy: Central 95%, Lakeside 90%, Hillview 85%, Westhaven 80%, Riverside 75%, Meadow 65%.

Riverside's 12 October waiting total has a correction: count revision 2, not both versions. Hillview has an extra posting withdrawn by a later revision: exclude it. Westhaven is missing 18 September, with incomplete coverage declared for that month. Meadow has zero outpatient visits on 16 August: no average exists for that day, but longer periods with visits can still be evaluated. October is complete for all six hospitals.

## Recreate and check

From `demo/`:

```sh
venv/bin/python scripts/prepare_hospital_data.py
venv/bin/python -c 'from scout.knowledge_index import build_indexes; build_indexes()'
venv/bin/python -m unittest discover -s tests -p test_hospital_data.py -v
```

The script replaces Cedar data only, preserving other companies. Run it after the older `create_demo_data.py` / `prepare_sector_data.py` preparation if resetting the whole demo. The older sector example file is the original small seed; the active, expanded dataset is in this directory.
