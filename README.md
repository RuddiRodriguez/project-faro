# Project Faro

Ask an English question about connected English-language company data, clarify it when necessary, and receive a checked answer in English with the files used to produce it. Language detection and translation are outside the current demo.

Faro is a working local demo for an AI engineering assessment. The same services run terminal, retail, hospital and hotel examples. A separate connector reads JSON, SQLite, Excel, CSV, Parquet and text PDFs. It is not a production identity system or a universal reader for every source.

## Start the demo

The current execution boundary is **macOS**: Bridge uses the operating system sandbox for model-generated pandas expressions. Other systems refuse these reads until an equivalent isolated worker is provided.

From a checkout:

    cd demo
    conda env create --prefix ./venv --file environment.yml
    conda activate ./venv
    python -m pip install -r requirements.txt
    cp .env.example .env
    # Set OPENAI_API_KEY in .env.
    python scripts/prepare_scout_model.py
    python console.py --test

The tested environment uses Python 3.15.2. Dependencies are pinned in the service packages. The model account must support the configured OpenAI models and Decision API; an arbitrary account is not assumed to have access.

The preparation command downloads the pinned public [multilingual E5 small checkpoint](https://huggingface.co/intfloat/multilingual-e5-small) ; Scout builds and saves indexes from connected source descriptions and PDF text on first use. To use existing compatible weights instead:

    python scripts/prepare_scout_model.py --weights /path/to/e5/weights

Weights, indexes, credentials, generated document copies and saved conversations stay outside Git. Fixtures are included. All example company information is fictional.

The console starts ten local APIs and closes them on exit. Log in with a demo account:

| User | Data | Example |
|---|---|---|
| maria | Terminal operations | Which berths had the most crane idle hours last month? |
| sam | Retail | How many units did all our stores sell in October 2026? |
| hospital_ops | Six hospitals, July–October | Compare hospital bed occupancy in October 2026, highest first. |
| riverside_manager | Riverside only | How many outpatient visits did Riverside record in October 2026? |
| hotel_hq | Three hotels | How many hotels do we have? |

Use /new for a fresh question, /logout to change account, /quit to stop. “Last month” uses the current UTC date. Tests may set FARO_REFERENCE_DATE for a reproducible date. A normal answer is followed only by Document: and Open: links. --test additionally shows timing, attempts and cache use.

## How it works

1. Compass coordinates the request. Gate checks the selected account and access; Connector lists the permitted sources.
2. Thread combines relevant replies. Scout combines meaning search with word search over field names and connected PDF passages. Passages retain page and character positions and are passed to Bridge as navigation hints, never as verified answers.
3. Signal classifies the next action. Guide asks a clarification only when a user choice is needed.
4. Bridge reads permitted evidence through Connector.
5. Shield repeats the reads and checks proposed findings. Voice presents the supported answer and document links.

Compass saves every turn in a company-specific data collection. The demo uses Parquet; the proposal describes SQL tables. Successful work is reused only for matching inputs and access. Shield rechecks cached evidence.

Model calls go through shared utils. Prompts use a consistent structure: role, objective, initial analysis, final reasoning and response. Pydantic defines the structured result beside its prompt. Short initial_analysis and reasoning summaries are saved per model call and attempt. These are decision explanations, not private chain-of-thought logs. Signal uses three choices in one Decision API call: action, assessment and justification.

## Code names follow responsibilities

Each service retains separate API and library folders, with shared Pydantic API objects in demo/api_objects.

| Service | Main library / class | Method |
|---|---|---|
| Compass | orchestrator.py / Orchestrator | orchestrate |
| Gate | access_checker.py / AccessChecker | check |
| Thread | rewriter.py / Rewriter | rewrite |
| Scout | searcher.py / Searcher | search |
| Signal | classifier.py / Classifier | classify |
| Guide | generator.py / Generator | generate |
| Bridge | reader.py / Reader | read |
| Shield | verifier.py / Verifier | verify |
| Voice | generator.py / Generator | generate |
| Connector | source_reader.py / SourceReader | read |

The search library and shared model utilities are included in the repository. Old ranking-only and fixed-field conversation endpoints were removed from Faro.

## Reuse and limits

The client provides data access and asks questions. Connection locations and access settings live in Connector; accounts and permissions live in Gate. Formats and permissions are configured outside the question services. Client meanings come from available documents and fields. No crane, hotel or hospital keyword rules select an analysis. Tests also use recycling and arbitrary field names.

That does **not** mean any client can connect any file and obtain a correct answer:

- There is no glossary, supported-task list or prepared business model to supply. JSON sources contain named tables of records; their field names remain unchanged.
- Native readers support local SQLite, header-row Excel/CSV, Parquet and text PDFs. They read all permitted rows without the former 1,000-row cap.
- SQLite, Excel and PDF connections grant whole-file access. JSON, CSV and Parquet connections can restrict rows by a configured access field. Gate is demo user selection; internal APIs trust the local coordinator. Production authentication and source-specific authorization still need implementation.
- Bridge links two tables using exact keys and requires an unambiguous complete match. Time-overlap joins, scanned PDFs, remote data lakes and MongoDB require additional support.
- A model may choose a poor read or decline an answerable question. Shield replay and evidence review reduce risk; they do not prove source truth.
- The sandbox has not undergone a production security audit.

## Test and inspect

From demo/:

    python scripts/run_tests.py

Paid, real console run across four sectors:

    FARO_RUN_LIVE_TESTS=1 python -m unittest discover -s tests -p test_sector_console.py -v

Local tests cover permissions, corrections, withdrawals, incomplete records, unfamiliar fields, source formats, document snapshots, execution boundaries, caches, retries and saved summaries. Live tests are explicit opt-ins. See [validation results](docs/validation.md) for exact coverage and limits.

- [Delivery proposal](output/pdf/terminal_data_proposal.pdf)
- [Proposal with Faro code references](output/pdf/terminal_data_proposal_with_project_references.pdf)
- [Hospital data](demo/local_data/demo_dataset/HOSPITAL_DATA.md)
- [Connector interface](demo/connector/machine-learning-connector-api/README.md)
- [Code reuse](demo/REUSE_REVIEW.md)
- [Changes and decisions](docs/release_review.md)

Rebuild PDFs with: demo/venv/bin/python docs/pdf/build_proposal.py

The root PowerPoint files are earlier presentation drafts; the PDFs are the maintained proposal.

## Search evaluation

From the repository root:

    demo/venv/bin/python demo/scripts/evaluate_search.py --output tmp/search-evaluation.json

The labelled test documents cover English questions, exact identifiers and several sectors. This measures source retrieval separately from answer correctness. Add `--rerank` to compare an extra local model (requires sentence-transformers and downloads the public cross-encoder checkpoint). It is an experiment, not part of the running services.

Search indexes change when permissions, source versions, embedding revision or passage format changes. CSV values remain text, preserving leading zeros and empty strings; Bridge can choose conversions during its read. Parquet keeps typed values. Both readers use the same permission, version and evidence checks as the existing formats.

See [search changes and before/after results](docs/search_improvements.md) for the implementation, measured results and remaining limitations.


## Local web demo

Run from the project folder:

```bash
demo/venv/bin/python demo/run_web_demo.py
```

Open http://localhost:8501. The launcher starts the ten APIs once, then opens the
Streamlit server. Stop it with Ctrl+C. The console remains available.

Choose a demo account, ask about its data, and reply in the same box when Faro
asks for clarification. “New question” clears the current question; “Switch account”
clears the displayed conversation before another account enters. Account selection
is for the local demo, not production authentication.

The web screen calls Gate and Compass. It displays Faro's answer unchanged and
provides source-document downloads, checked evidence, and saved timing, cache and
model-attempt details. Downloads are selected from the saved turn and checked against
the account's current permissions and the saved file's fingerprint. The browser never
supplies a file path. The UI adds no model calls or answer cache.

Install the web dependency with `demo/venv/bin/python -m pip install streamlit==1.66.1`
if the environment was created before this screen was added.

### Azure demo

[Open the deployed demo](https://faro-ruddigarcia-demo-dhdngebkgvf8bqc2.westus3-01.azurewebsites.net).
The recorded live Maria test is in `docs/validation/azure_deployment.json`.

`.github/workflows/azure-deploy.yml` deploys the tracked `demo/` files to the
`faro-ruddigarcia-demo` Linux Web App. It runs on changes to the demo on `main`,
or manually from GitHub Actions. The Linux requirements use CPU-only PyTorch.
Local `.env` files, environments and saved conversations are not packaged.

GitHub signs in through an Azure identity restricted to this Web App. The trust
matches this repository's permanent IDs and its `main` branch. No Azure password
or publish profile is stored in the repository.

`demo/start_azure.sh` starts the same ten APIs privately and exposes only the
Streamlit screen on port 8000. The first start downloads the pinned search model.
The model, search indexes, saved turns and source copies are kept under
`/home/faro`, so they survive application deployments. The demo source files are
included with the application. Account selection remains a demo sign-in.

The OpenAI key is an Azure application setting. The optional encrypted GitHub
secret `FARO_OPENAI_API_KEY` transfers it to Azure during deployment; removing
that secret afterward leaves the Azure setting in place. Never commit the key.
