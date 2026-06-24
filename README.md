# ⚡ AI App Compiler

An engineered compiler system that converts open-ended natural language requests into fully validated, consistent, and executable Node.js/Express/SQLite applications.

It guarantees structural validity and cross-layer integrity using a multi-stage pipeline, Pydantic type constraints, and a self-repair feedback engine.

---

## 🏗️ Architecture & Pipeline Design

A single prompt generation of a full-stack codebase is unreliable and prone to logical drift. The AI App Compiler handles code generation like a traditional programming language compiler: dividing the process into separate logical stages.

```
       [ Vague Prompt / Input ]
                  │
                  ▼
       [ 0. Clarification Engine ]  ◄── (Fast deterministic guard)
                  │
                  ▼
       [ 1. Intent Extraction ]     ── (Identify entities, pages, billing)
                  │
                  ▼
       [ 2. System Design / Arch ]  ── (Define data schemas, flows, roles)
                  │
                  ▼
       [ 3. Schema Generation ]     ── (Generate UI, API, DB, Auth, Logic)
                  │
                  ▼
       [ 4. Refinement Layer ]      ── (Align references & variables locally)
                  │
                  ▼
       [ 5. Validation & Repair ]   ── (Validate Pydantic & repair loops)
                  │
                  ▼
       [ 6. Codegen / Runtime ]     ── (Compile to runnable Node.js app)
```

1. **Stage 0: Clarification Guard**: A fast, local rule engine that blocks extremely vague inputs (e.g., `"CRM"`, `"app"`) and asks specific clarification questions immediately in `< 10ms`.
2. **Stage 1: Intent Extraction**: Parses the prompt into a high-level list of features, pages, entities, and billing specifications.
3. **Stage 2: System Design Layer**: Conceptualizes the application architecture: entities, fields, relationships, and user roles.
4. **Stage 3: Schema Generation**: Generates 5 distinct schemas matching specific Pydantic schemas:
   * **UI Schema**: Page routing, components, layout grids, actions.
   * **API Schema**: Endpoints, HTTP methods, input parameters, validator rules.
   * **DB Schema**: Tables, columns, datatypes, foreign keys.
   * **Auth Schema**: Role definitions, permissions, read/write matrices.
   * **Business Logic**: Premium gate checks, payment rules, custom business limits.
5. **Stage 4: Refinement Layer**: Programmatically checks cross-layer consistency (e.g., ensuring API endpoints exist for UI components, and table fields exist for API queries).
6. **Stage 5: Validation & Repair**: Validates JSON types against Pydantic models. If constraints fail, it triggers targeted LLM repair loops (max 3 loops) feeding the error logs back to the LLM to fix the specific schema piece.
7. **Stage 6: Codegen Engine**: Compiles the schemas using Jinja2 templates into a fully runnable Node.js application (Express server, SQLite DB, authentication middleware, JWT signup/login, CRUD routes) packaged into a downloadable `.zip` file.

---

## 📂 Project Directory Structure

```
.
├── Dockerfile                  # Containerizes backend + Node.js runtime
├── docker-compose.yml          # Container build and orchestration config
├── README.md                   # System documentation & Loom outline
├── TRADEOFFS.md                # Cost, latency, and quality tradeoffs analysis
├── EVAL_REPORT.md              # Markdown output of the evaluation run
├── evaluation_results.json     # Dataset telemetry results from the runner
├── frontend/                   # Premium Glassmorphism UI
│   ├── index.html              # Demo client page
│   ├── style.css               # Styling and progress trackers
│   └── app.js                  # Async poll request controller
└── backend/                    # Python FastAPI Backend
    ├── requirements.txt        # python dependencies
    ├── scripts/
    │   ├── run_eval.py         # CLI evaluation runner
    │   └── test_schemas.py     # Simple schema testing script
    └── app/
        ├── main.py             # FastAPI endpoints & static file serving
        ├── config.py           # Environment and model configuration
        ├── llm/
        │   └── client.py       # OpenAI/Groq client with retry middleware
        ├── pipeline/
        │   ├── orchestrator.py # Pipeline Orchestrator coordinator
        │   ├── clarification.py# Pre-LLM clarification validator
        │   ├── intent_extraction.py
        │   ├── architecture_design.py
        │   ├── schema_generation.py
        │   ├── refinement.py   # Local cross-layer consistency checks
        │   ├── validation_repair.py # Pydantic parser & repair engine
        │   └── prompts.py      # Targeted LLM system prompts
        ├── schemas/            # Pydantic schemas enforcing output contract
        │   ├── pipeline_state.py
        │   ├── intent.py, architecture.py, ui_schema.py, api_schema.py...
        └── codegen/            # Jinja2 template-to-Node compiler
            ├── generator.py
            └── templates/      # db.js, package.json, server.js, auth middleware...
```

---

## 🚀 Quick Start Guide

### Option 1: Running Locally (Fastest)

#### 1. Setup Environment
Python 3.10+ is recommended. Create a virtual environment and activate it:
```powershell
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install requirements:
```bash
cd backend
pip install -r requirements.txt
```

#### 2. Configure environment variables
Create a `.env` file inside the `backend/` directory:
```env
GROQ_API_KEY=your-groq-api-key-here
MODEL_NAME=llama-3.3-70b-versatile
GENERATED_APPS_DIR=./generated_apps
```

#### 3. Run server
Start the FastAPI server using uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
Open `http://localhost:8000` in your browser to access the beautiful compiler UI.

---

### Option 2: Running with Docker (Recommended for Staging)

Ensure Docker Desktop is installed. From the workspace root:

```bash
# Set your API Key in your console session
# Windows PowerShell:
$env:GROQ_API_KEY="your-groq-api-key"
# macOS/Linux:
export GROQ_API_KEY="your-groq-api-key"

# Build and start the container
docker-compose up --build
```
Access the application dashboard at `http://localhost:8000`.

---

## 🧪 Evaluation Framework

The system includes a benchmarking runner to track reliability metrics against a set of 10 real product prompts and 10 edge cases (vague, conflicting, incomplete).

To run evaluations:
```bash
# Navigate to the backend folder
cd backend

# Run in Mock mode (runs locally, zero-cost simulation)
python scripts/run_eval.py --mode mock

# Run in Real mode (hits Groq API, requires GROQ_API_KEY configured)
python scripts/run_eval.py --mode real
```

Outputs will be saved in the root workspace folder:
* `evaluation_results.json` - telemetry data.
* `EVAL_REPORT.md` - comprehensive markdown breakdown of success rates and repairs.

---

## 📡 API Endpoint Reference

| Endpoint | Method | Description |
|:---|:---|:---|
| `/health` | `GET` | Health check and active LLM configuration |
| `/compile` | `POST` | Synchronous compiler run (takes 20-40s depending on model) |
| `/compile/async` | `POST` | Asynchronous trigger. Returns a `request_id` instantly |
| `/compile/status/{id}` | `GET` | Polls the current compile state, progress percentage, and schema updates |
| `/apps/{id}/download` | `GET` | Returns a compiled `.zip` file of the Node.js application |

---

## 🎥 Loom Video Presentation Outline (5-10 Minutes)

Use this outline to record a high-scoring Loom video submission:

### 1. Introduction (0:00 - 1:00)
* Introduce yourself and state the core objective: building an **engineered compiler** (not a prompt engineering trick) that converts natural language to runnable apps.
* Present the live UI dashboard with custom dark glassmorphism and the pipeline tracker.

### 2. Architecture & Pipeline Design (1:00 - 3:00)
* Explain **why a multi-stage approach** is mandatory: context limits, logical drift, and schema consistency.
* Briefly walk through the files: `Clarification Engine -> Intent -> Architecture -> Schemas -> Local Refinement -> Validation/Repair -> Codegen`.
* Highlight the local programmatic **Refinement Layer** which aligns endpoints and databases without paying LLM token costs.

### 3. The Core: Validation & Repair Engine (3:00 - 5:00)
* Walk through `backend/app/pipeline/validation_repair.py`.
* Show how schema checks against Pydantic models are captured.
* Explain the **Self-Repair Loop**: how validation errors (JSON schema violations, type mismatch) are fed back into targeted LLM prompts to self-heal.
* Show the deterministic **Stage 0 Clarification** guard preventing vague requests from consuming LLM cost.

### 4. Tradeoffs & Cost vs. Quality (5:00 - 7:00)
* Discuss the analysis in `TRADEOFFS.md`.
* Explain why **Llama 3.3 70B on Groq** was chosen: ~80 tokens/sec speed combined with sub-cent cost per application compilation (~$0.0098) compared to Claude or GPT-4o.
* Detail how Pydantic type safety + local codegen templates compensate for model size constraints to guarantee executable output.

### 5. Demo & Runtime Validation (7:00 - 9:00)
* Put a complex prompt in the UI (e.g. CRM with payment tiers and admin analytics).
* Walk through the real-time progress tracker.
* Review the compiled JSON output tabs (UI, DB, API, Auth, Logic) showcasing syntax highlighting.
* Download the `.zip` file, extract, and briefly show the generated Express/SQLite code proving **execution awareness**.