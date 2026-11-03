# Faro demo

See the [project README](../README.md) for installation, accounts, architecture, service names, tests and limitations.

Run the console from this directory:

    venv/bin/python console.py --test

It starts eleven APIs, prompts for a demo user and stops those APIs on exit.

- [Connector example](connector/machine-learning-connector-api/README.md)
- [Hospital data](local_data/demo_dataset/HOSPITAL_DATA.md)
- [Shared model utilities](utils/README.md)
- [Saved turns and model calls](compass/machine-learning-compass-api/DATA_COLLECTION.md)
- [Reuse review](REUSE_REVIEW.md)

Fixtures are checked in. Prepare indexes with scripts/prepare_scout_model.py. To reset hospital data, run scripts/prepare_hospital_data.py and rebuild indexes. The old whole-dataset generator resets the fixtures; do not run it unless that is intended.
