# Faro demo

One shared Conda environment. Separate folders for each service. Compass calls Gate, Library, Thread, [Scout](scout/machine-learning-scout-api/README.md), [Signal](signal/machine-learning-signal-api/README.md), [Guide](guide/machine-learning-guide-api/README.md), [Bridge](bridge/machine-learning-bridge-api/README.md), [Shield](shield/machine-learning-shield-api/README.md) and [Voice](voice/machine-learning-voice-api/README.md) through their APIs. Gate provides demo user selection, not real sign-in. See [Thread instructions](thread/machine-learning-thread-api/README.md), [utils notes](utils/README.md), [Compass instructions](compass/machine-learning-compass-api/README.md), [Gate instructions](gate/machine-learning-gate-api/README.md) and [Library instructions](library/machine-learning-library-api/README.md).

[Service-by-service API and library reuse review](REUSE_REVIEW.md)

## Try the console

From the demo folder, run `venv/bin/python console.py`. It starts all eleven APIs on local ports, waits for them, then asks for a demo user. Enter an active user ID such as maria, sam, hospital_ops or hotel_hq. Gate checks the selected account; this local demo does not use passwords. Use /logout to switch accounts and start with no conversation history. Type `/quit` to exit and stop those APIs. No separate terminals needed.

For a visible test, run `venv/bin/python console.py --test`. Ask “Which cranes performed badly last month?” When Faro asks for more detail, reply “North Terminal, downtime, highest first.” To test reuse, enter `/new`, ask “Rank North Terminal cranes by highest downtime last month.” Then enter `/new` and ask that exact question again. Each turn shows the full question, recorded time and which services reused saved work. This runs the real services and may call the configured model.

## Environment

Python 3.15.2, standard CPython build.

```sh
cd /Users/ruddigarcia/Projects/assesment/demo
conda activate ./venv
```

To recreate the environment:

```sh
conda env create --prefix ./venv --file environment.yml
```

## Services

- compass: coordinates services
- gate: checks identity and access
- library: holds company information
- thread: combines the question and replies
- scout: searches company information
- signal: classifies the next action
- guide: asks follow-up questions
- bridge: gets relevant data
- shield: checks facts and answers
- voice: writes the answer
- Compass saves turns and reusable work in the [company data collection](compass/machine-learning-compass-api/DATA_COLLECTION.md).

Each service has a `machine-learning-<service>-api` folder, API folders under `infer/src`, and a library folder at `infer/<service>/<service>`, following the Japan API/library layout. The API and library folders are reserved for separate repositories; Git repositories and submodules are not initialised yet.

Build services one by one, reusing existing code. Keep code simple and avoid unnecessary checks or layers. All services use the root Conda environment; dependencies will be selected as each service is implemented.

[Try four sectors](local_data/sector_examples/README.md): same services for port operations, retail, hospitals and a multinational hotel chain. Thread resolves clarification replies and short follow-ups about the previous verified data question. Bridge receives the question and the full permitted catalogue. Through utils it can request multiple pandas reads and inspect their results before returning findings. Shield replays the reads and checks the evidence for each finding.

**Question flow:** Ask a direct question about a company measure. If a required detail is missing,
Guide asks one direct question. If another detail is still missing, it asks again, keeping the choices already made. Faro reads the permitted records, checks
the findings, and returns a supported answer or a specific limitation. The console carries only the last verified question into the next request, so “and how many per terminal?” can refer to the previous subject. /new clears that context. Completed turns remain in the data collection; only opening questions can reuse cached work.

When you run the console with `--test`, it also shows each service's model attempts. The same information is in `turns[].model_attempts` in a conversation export. Under each service, `calls` contains one list per model call; entries inside a list are its attempts in order. For example, `[["timeout","success"],["success"]]` means two separate calls, three attempts, and one successful retry. A service that did not call a model has no entry. Older turns without tracking show `null`, not zero.

Each service writes its own call row in the demo's shared Parquet collection (`company/model_calls/turn_id/`). Counts come from the model calls, not from how long Compass waited. A running attempt shows `in_progress`; if a service stops before recording its outcome, it stays that way. Exporting the turn again reads the latest outcomes.

[Connector service and three-source example](connector/machine-learning-connector-api/README.md): sign in as Maria and ask “Which berths had the most crane idle hours last month?” Scout discovers permitted items; Bridge and Shield use the same connector API for reads and verification.
