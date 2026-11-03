# Project Faro

Ask a question about company data, clarify it when necessary, and receive a checked answer with the files used to produce it.

Faro is a working local demo for an AI engineering assessment. The same services run terminal, retail, hospital and hotel examples. A separate connector reads SQLite, Excel and text PDFs. It is not a production identity system or a universal reader for every source.

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

The preparation command downloads the pinned public [multilingual E5 small checkpoint](https://huggingface.co/intfloat/multilingual-e5-small) and builds one company search index. To reuse your existing Luna weights instead:

    python scripts/prepare_scout_model.py --weights /path/to/e5/weights

Weights, indexes, credentials, generated document copies and saved conversations stay outside Git. Fixtures are included. All example company information is fictional.

The console starts eleven local APIs and closes them on exit. Log in with a demo account:

| User | Data | Example |
|---|---|---|
| maria | Terminal operations | Which berths had the most crane idle hours last month? |
| sam | Retail | How many units did all our stores sell in October 2026? |
| hospital_ops | Six hospitals, July–October | Compare hospital bed occupancy in October 2026, highest first. |
| riverside_manager | Riverside only | How many outpatient visits did Riverside record in October 2026? |
| hotel_hq | Three hotels | How many hotels do we have? |

Use /new for a fresh question, /logout to change account, /quit to stop. “Last month” uses the fixture's reference clock, 1 November 2026; it is not the machine's live date. A normal answer is followed only by Document: and Open: links. --test additionally shows timing, attempts and cache use.

## How it works

1. Compass coordinates the request. Gate checks the selected account and access; Library supplies permitted company information.
2. Thread combines relevant replies. Scout searches definitions and discovers connected sources.
3. Signal classifies the next action. Guide asks a clarification only when a user choice is needed.
4. Bridge reads permitted evidence through the Connector or the prepared JSON reader.
5. Shield repeats the reads and checks proposed findings. Voice presents the supported answer and document links.

Compass saves every turn in a company-specific data collection. The demo uses Parquet; the proposal describes SQL tables. Successful work is reused only for matching inputs and access. Shield rechecks cached evidence.

Model calls go through shared utils. Prompts follow Japan/Gambit: role, objective, initial analysis, final reasoning and response. Pydantic defines the structured result beside its prompt. Short initial_analysis and reasoning summaries are saved per model call and attempt. These are decision explanations, not private chain-of-thought logs. Signal uses three choices in one Decision API call: action, assessment and justification.

## Code names follow responsibilities

Each service retains separate API and library folders, with shared Pydantic API objects in demo/api_objects.

| Service | Main library / class | Method |
|---|---|---|
| Compass | orchestrator.py / Orchestrator | orchestrate |
| Gate | access_checker.py / AccessChecker | check |
| Library | information_reader.py / InformationReader | read |
| Thread | rewriter.py / Rewriter | rewrite |
| Scout | searcher.py / Searcher | search |
| Signal | classifier.py / Classifier | classify |
| Guide | generator.py / Generator | generate |
| Bridge | reader.py / Reader | read |
| Shield | verifier.py / Verifier | verify |
| Voice | generator.py / Generator | generate |
| Connector | source_reader.py / SourceReader | read |

Copied Nemo search and original model utilities retain their source names. Old ranking-only and fixed-field conversation endpoints were removed from Faro.

## Reuse and limits

Formats and permissions are configured outside the question services. Client meanings come from available documents and fields. No crane, hotel or hospital keyword rules select an analysis. Tests also use recycling and arbitrary field names.

That does **not** mean any client can connect any file and obtain a correct answer:

- The JSON path expects the prepared inventory/daily-record structure. Native connector reads do not require those business fields.
- Native readers support local SQLite, header-row Excel and text PDFs, at most 500 rows per item. Larger reads stop; they do not silently sample.
- Connections grant whole-file access. Gate is demo user selection; internal APIs trust the local coordinator. Production authentication and row-level authorization are not implemented.
- Bridge links two tables using exact keys and requires an unambiguous complete match. Time-overlap joins, scanned PDFs, remote data lakes and MongoDB require additional support.
- A model may choose a poor read or decline an answerable question. Shield replay and evidence review reduce risk; they do not prove source truth.
- The sandbox has not undergone a production security audit.

## Test and inspect

From demo/:

    python scripts/run_tests.py

Paid, real console run across four sectors:

    FARO_RUN_LIVE_TESTS=1 python -m unittest discover -s tests -p test_sector_console.py -v

Optional comparison with original private repositories:

    FARO_CHECK_ORIGINAL_REPOS=1 python -m unittest discover -s utils/tests -v

Local tests cover permissions, corrections, withdrawals, incomplete records, unfamiliar fields, source formats, document snapshots, execution boundaries, caches, retries and saved summaries. Live tests are explicit opt-ins. See [validation results](docs/validation.md) for exact coverage and limits.

- [Delivery proposal](output/pdf/terminal_data_proposal.pdf)
- [Personal proposal with references](output/pdf/terminal_data_proposal_with_project_references.pdf)
- [Hospital data](demo/local_data/demo_dataset/HOSPITAL_DATA.md)
- [Connector interface](demo/connector/machine-learning-connector-api/README.md)
- [Code reuse](demo/REUSE_REVIEW.md)
- [Changes and decisions](docs/release_review.md)

Rebuild PDFs with: demo/venv/bin/python docs/pdf/build_proposal.py

The root PowerPoint files are earlier presentation drafts; the PDFs are the maintained proposal.
