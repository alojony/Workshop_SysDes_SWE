Compliance Q&A Compliance Dashboard Workshop (Revised)

Format: 6 sessions · ~2h each
Medium: Discord + screenshare + beer
Stack: Python + FastAPI + Postgres · Docker only in Session 6
Philosophy: Design first → DB-first → build dirty → engineer it clean → expose Q&A via API → plug UI → containerize.

⸻

0) What you (host) should prepare upfront

These are the “scaffolding” items so sessions stay focused on systems learning, not tool misery.

A. Repo skeleton (give them on Day 0)

compliance-dashboard/
├─ docs/
├─ data/
│  ├─ raw/                 # incoming mock files (csv/pdf)
│  └─ samples/             # optional sample sets
├─ app/                    # FastAPI app
│  ├─ main.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ settings.py
│  └─ routes/
├─ worker/
│  ├─ ingest_dirty.py       # they build in Session 3
│  ├─ normalize.py          # rules (Session 4)
│  └─ ingest_clean.py       # improved ingestion (Session 4)
├─ queries/
│  ├─ qa.sql                # reference SQL
│  └─ qa.py                 # query functions
├─ ui/                      # optional: prebuilt stub UI to plug into API
├─ scripts/
│  ├─ init_db.py
│  └─ reset_db.py
├─ docker/
│  ├─ Dockerfile.api        # you can pre-write
│  ├─ Dockerfile.ui         # optional
│  └─ docker-compose.yml    # Session 6
├─ .env.example
└─ README.md

B. Mock data pack (you provide)
	•	A folder with:
	•	inspection_logs.csv
	•	maintenance_logs.csv
	•	ncr_reports.csv
	•	/pdf/ with a few inspection + NCR PDFs

C. Your “golden reference” ingestion code

You’ll share this after Session 2 so they can compare reality vs their dirty implementation.

D. Minimal UI stub (optional)
	•	Either a tiny HTML page or a prebuilt Angular/React skeleton that only needs API endpoints wired.

⸻

Non-negotiable rules
	•	Session 1: no code.
	•	DB schema must support the questions.
	•	Ingestion must be idempotent (re-running doesn’t duplicate).
	•	Errors are data: failures must be visible and queryable.
	•	Docker only in Session 6.

⸻

Canonical Q&A targets (what the dashboard must answer)
	1.	Failed inspections in a date range (filters: site/line/supplier/part)
	2.	NCRs open beyond SLA (e.g., > 30 days) + severity breakdown
	3.	Top failure sources (supplier, machine, part)
	4.	Evidence view: given NCR, show linked inspection + raw document references
	5.	Ingestion health: what failed processing and why (by stage)
	6.	Trend view: failures per week/month

⸻

SESSION 1 – Requirements, Schema Draft, and API Contract (No Code)

Theme: Think like an auditor, not a tutorial follower.

Inputs
	•	Sample CSV/PDF set (just to glance at structure)

Objectives
	•	Agree on the questions
	•	Draft the DB schema (on paper)
	•	Draft the API petitions/requests (contract-first)

Agenda
	•	Define ~10–12 compliance questions; select 6 “must-have” (see targets above)
	•	Schema draft: entities, keys, relationships, status lifecycle
	•	Define processing stages and what gets logged
	•	Draft API petitions (request/response shapes)

Expected artifacts
	•	docs/questions.md
	•	docs/schema_draft.md (tables + fields + relationships)
	•	docs/api_contract.md (endpoints + payloads)

API contract (minimum set)
	•	GET /health
	•	GET /qa/failed-inspections?from=&to=&site=&supplier=&part=
	•	GET /qa/open-ncrs?older_than_days=&severity=
	•	GET /qa/top-failures?group_by=supplier|machine|part&from=&to=
	•	GET /qa/evidence?ncr_id=
	•	GET /ops/ingestion-runs?status=&stage=&from=&to=

Learning challenges
	•	Force precision: every field exists because a question demands it
	•	Separate “raw truth” from “derived/normalized truth”

⸻

SESSION 2 – Build the Database First (Local, No Docker)

Theme: The DB is the backbone.

Objectives
	•	Implement schema in Postgres (locally installed) or SQLite→Postgres if needed
	•	Add constraints, enums, and relationships
	•	Seed nothing yet (empty DB is fine)

Expected code you should prep (host)
	•	scripts/init_db.py and/or migration files in migrations/
	•	.env.example with DB connection string

What they implement
	•	Tables (v1):
	•	documents (id, source, filename, path, checksum, received_at)
	•	processing_runs (id, document_id, stage, status, error, started_at, finished_at)
	•	inspections (facts)
	•	ncrs (facts + lifecycle + linked_inspection_id)
	•	maintenance_events (facts)

Acceptance criteria
	•	DB can be created from scratch with one command
	•	Constraints prevent obvious garbage
	•	Relationships enforce traceability

Deliverables
	•	docs/schema.md (finalized)
	•	Schema code committed

⸻

SESSION 3 – Build Dirty Ingestion (Local, Ugly, Running)

Theme: Make it work. Then you’ll discover why it’s hard.

Inputs
	•	Your mock data pack in data/raw/

Objective

Write a crude pipeline that:
	•	discovers files
	•	registers them in documents
	•	creates processing_runs
	•	loads CSV rows into tables (even if messy)

Expected code modules
	•	worker/ingest_dirty.py
	•	scan_folder()
	•	hash_file()
	•	register_document()
	•	record_run(stage, status, error)
	•	load_csv_*()

Minimum stages to track
	•	RECEIVE
	•	PARSE_CSV
	•	PERSIST

Acceptance criteria
	•	Running ingestion twice does not duplicate documents (checksum or filename+size heuristic)
	•	Failures don’t crash entire run; they are recorded in processing_runs

Learning challenges
	•	Idempotency
	•	Partial failures
	•	Realizing how inconsistent CSVs are

Host action

After they demo the dirty version, you share your “golden reference” ingestion to compare designs.

⸻

SESSION 4 – Engineer It Clean (Normalization + Robust Ingestion)

Theme: Stop dumping mud into the river.

Objectives
	•	Define normalization rules
	•	Implement validation + normalization layer
	•	Improve pipeline stages and error classification

Normalization rules to teach (minimum)
	•	Date parsing and timezone policy
	•	Units normalization (mm/%/etc.)
	•	Status enums: PASS/FAIL, OPEN/CLOSED
	•	Deduplication keys for domain rows (e.g., inspection_id)
	•	Handling missing data (nullable vs default vs reject)

Expected code modules
	•	worker/normalize.py
	•	normalize_dates()
	•	normalize_units()
	•	normalize_status()
	•	validate_row()
	•	worker/ingest_clean.py
	•	staged processing
	•	transaction boundaries
	•	row-level error capture

New stages
	•	NORMALIZE
	•	VALIDATE

Acceptance criteria
	•	“Clean ingestion” produces consistent rows
	•	Bad rows are quarantined (logged) without blocking everything
	•	Re-run is safe

Deliverables
	•	docs/normalization_rules.md
	•	Cleaner ingestion committed

⸻

SESSION 5 – API Petitions + CLI Dashboard (No UI Yet)

Theme: Answers first. UI later.

Objectives
	•	Implement FastAPI endpoints defined in Session 1
	•	Back endpoints with query functions
	•	Provide a CLI that calls endpoints and prints results (cyberpunk optional)

Expected code modules
	•	app/main.py (FastAPI app)
	•	app/routes/qa.py (endpoints)
	•	queries/qa.py (query functions)
	•	cli/qa_cli.py (simple argparse client)

Endpoint acceptance criteria
	•	Each of the 6 canonical Q&A targets is answerable via an API call
	•	Responses include evidence references:
	•	document_id
	•	filename/path
	•	linked IDs (inspection_id, ncr_id)

CLI acceptance criteria
	•	python -m cli.qa_cli failed-inspections --from ... --to ...
	•	outputs readable tables or JSON

Deliverables
	•	docs/api_examples.md with example requests + sample outputs

⸻

SESSION 6 – UI Plug-in + Docker Packaging (Basic)

Theme: Make it reproducible on Windows + macOS.

Objectives
	•	Plug a simple UI into the API
	•	Containerize backend + db + ui (if any)
	•	Produce a one-command run

UI options (pick one)
	•	Minimal HTML/JS fetching endpoints
	•	Streamlit UI
	•	Prebuilt Angular/React skeleton (host-provided) where they only wire endpoints

Expected docker assets (host can pre-write)
	•	docker/docker-compose.yml
	•	db (postgres)
	•	api (FastAPI)
	•	ui (optional)
	•	docker/Dockerfile.api
	•	docker/Dockerfile.ui (optional)

Compose acceptance criteria
	•	docker compose up starts everything
	•	UI can query API
	•	API can reach DB

Final demo: mini audit

You ask 5 questions live:
	•	show overdue NCRs and evidence
	•	show failures per week
	•	prove a closure chain (NCR → Inspection → Raw doc)
	•	show ingestion failures
	•	show top failure source

Deliverables
	•	docs/runbook.md (local + docker run steps)
	•	working compose stack

⸻

Outcome (what they should walk away with)
	•	How to start with questions and derive a schema
	•	How ingestion pipelines fail in real life
	•	How normalization rules make systems usable
	•	How to expose “answers” via API before UI
	•	How to package for reproducibility only once understanding exists
