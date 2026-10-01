# Signal — Exa-Powered Thesis Intelligence

> **Turn an investment thesis into continuously researched web signals.**

Signal is a buy-side equity research tool that converts investment thesis assumptions into semantic web signals, researches them with Exa, enriches ambiguous findings with the Exa Agent, and surfaces only analyst-approved evidence into the persistent thesis evidence base.

---

## Problem

Buy-side analysts already have Bloomberg, FactSet, Excel, earnings transcripts, and financial models.

Signal addresses a different problem: **investment thesis assumptions depend on information scattered across the open web** — customer announcements, competitor websites, job postings, technical blogs, regulatory filings, hiring activity, developer ecosystems.

The analyst wants to know: *"Did something happen on the web that strengthens, weakens, or changes something I believe about this company?"*

---

## Product

**Signal** converts an analyst's investment thesis into custom semantic signals that Exa can discover, research, enrich, validate, structure, and continuously monitor.

### Core Workflow

```
Investment Thesis
        ↓
Thesis Assumptions
        ↓
Custom Signals  (analyst-defined semantic conditions)
        ↓
Exa Search  (broad discovery — candidate evidence)
        ↓
Candidate Evidence  (not yet truth)
        ↓
Exa Agent  (deep research, enrichment, structured validation)
        ↓
Enrichment + Validation  (structured output with citations)
        ↓
Analyst Approval  (human gate — nothing enters thesis automatically)
        ↓
Thesis Evidence Base  (persistent, directional, sourced)
```

### Search vs Agent vs Monitor

| Tool | Role | When to use |
|------|------|-------------|
| **Exa Search** | Broad discovery | Find pages matching a research question |
| **Exa Agent** | Deep investigation | Validate, enrich, structure a specific candidate |

---

## Why Exa

Signal uses Exa as the core research infrastructure — not as a wrapper around a single search bar.

### Exa Search (`POST /search`)
- **Search modes**: `instant`, `fast`, `auto`, `deep-lite`, `deep`, `deep-reasoning`
- **Content retrieval**: `highlights`, `text`, `summary`
- **Structured outputs**: `outputSchema` with synthesized JSON
- **Domain control**: `includeDomains`, `excludeDomains`
- **Publication dating**: `startPublishedDate`, `endPublishedDate`
- **Categories**: `news`, `company`, `publication`, `financial report`, `people`, `personal site`
- **Research context**: `objective` (what makes a result useful), `systemPrompt` (source preferences, deduplication rules)

### Exa Agent (`POST /agent/runs`)
- **Effort tiers**: `minimal` ($0.012) → `low` → `medium` ($0.10) → `high` → `xhigh` ($1.00) → `auto`/`ultra`
- **Structured outputs**: `outputSchema` (JSON Schema) returned in `output.structured`
- **Input enrichment**: `input.data` — pass existing search records to Agent for row-level enrichment
- **Field-level grounding**: citations per output field with confidence levels
- **Async polling**: run ID + poll until completed

### API Limitations Discovered
- `snapshotAsOf` — **not in current Exa Search API**. UI shows a graceful note rather than fabricating behavior.
- `company` and `people` categories — **do not support** `startPublishedDate`, `endPublishedDate`, or `excludeDomains`. UI dynamically disables those controls.

---

## Architecture

```
React 18 + Vite + TypeScript + Tailwind CSS
        ↓  (TanStack Query, Axios)
FastAPI 0.111 + Python 3.12
        ↓
Research Orchestration Layer
    ├── Exa Search Service      (POST /search)
    └── Exa Agent Service       (POST /agent/runs, GET /agent/runs/{id})
        ↓
SQLite (SQLAlchemy + Alembic)
        ↓
Persistent Analyst Research State
```

---

## Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- An Exa API key from [dashboard.exa.ai](https://dashboard.exa.ai)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set EXA_API_KEY=your_key_here

# Start server (seeds NVDA demo data automatically)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Environment Variables

```env
# backend/.env
EXA_API_KEY=your_exa_api_key
DATABASE_URL=sqlite:///./signal.db
DEMO_MODE=false   # set true if no API key available
```

> **Security**: `EXA_API_KEY` is never exposed to the frontend. All Exa calls go through FastAPI.

---

## Demo Walkthrough (NVDA)

The app seeds with a complete NVIDIA demo out of the box:

**1. Thesis** — Open `/thesis/NVDA`
- Investment thesis with 5 structured assumptions
- Evidence status per assumption (Supporting / Mixed / Challenged / Insufficient)
- Click "Suggest Signals" to see AI-generated signal suggestions

**2. Signals** — Open `/signals/NVDA`
- 4 pre-seeded custom signals: ROCm Hiring, Alternative Accelerator Adoption, CUDA Expansion, Leadership Changes
- Each linked to a specific thesis assumption with expected direction

**3. Research (most important)** — Open `/research/NVDA`
- Type a research question, or click Research on a Signal
- Choose Search Mode (Auto / Fast / Deep / Deep Reasoning)
- Set result count, date range, include/exclude domains
- Add objective and system prompt in Advanced
- See **Exa Search Request Inspector** update in real-time on the right panel
- **Snapshot note**: shown inline as unavailable per current API
- Click **Search** → real Exa results with highlights, entities, source metadata

**4. Enrich a candidate**
- Select a result → click **Enrich**
- Agent drawer opens with effort selector, input.data preview, output schema
- Click **Investigate** → Exa Agent enriches with structured output + citations
- Decide: Supporting / Contradicting / Neutral → **Add to Thesis**

**5. Inbox** — Open `/inbox/NVDA`
- Review all candidate findings
- Enrich with Agent, approve into thesis, or dismiss

---

## Key Product Principles

- **No Bloomberg** — no charts, no financial models, no market data
- **No auto-updates** — nothing enters the thesis without analyst approval
- **Contradictory evidence matters** — every workflow supports all four directions
- **Exa is inspectable** — raw request JSON always visible; search strategy transparent
- **Search ≠ Agent** — Search discovers, Agent investigates

---

## API Reference

All endpoints at `http://localhost:8000/api/`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/companies` | List companies |
| GET | `/companies/{ticker}/thesis` | Get thesis + assumptions |
| PUT | `/theses/{id}` | Update thesis text |
| POST | `/theses/{id}/suggest-signals` | AI signal suggestions |
| GET | `/companies/{ticker}/signals` | List signals |
| POST | `/companies/{ticker}/signals` | Create signal |
| **POST** | **`/search`** | **Run Exa Search** |
| GET | `/search/config-info` | Search modes, categories, constraints |
| **POST** | **`/agent-runs`** | **Start Exa Agent run** |
| GET | `/agent-runs/{id}` | Poll agent run status |
| POST | `/agent-runs/{id}/wait` | Block until complete |
| **POST** | **`/search-results/{id}/enrich`** | **Enrich result with Agent** |
| POST | `/evidence` | Create evidence candidate |
| POST | `/evidence/{id}/approve` | Approve into thesis |
| GET | `/companies/{ticker}/inbox` | Inbox findings |

---

## Tests

```bash
cd backend
pytest tests/ -v
```

```bash
cd frontend
npm run build  # type check + production build
```
