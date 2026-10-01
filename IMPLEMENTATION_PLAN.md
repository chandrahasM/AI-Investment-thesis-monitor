# Signal — Implementation Plan

## Product Overview
Signal is an Exa-powered thesis intelligence platform for buy-side equity analysts.

## Exa API — Current Endpoints & Parameters (verified Sep 2026)

### Search (`POST https://api.exa.ai/search`)
- `query` (required)
- `type`: `instant` | `fast` | `auto` | `deep-lite` | `deep` | `deep-reasoning`
- `numResults`: 1–100
- `startPublishedDate`, `endPublishedDate`: ISO 8601
- `includeDomains`, `excludeDomains`: string arrays
- `category`: `company` | `publication` | `news` | `personal site` | `financial report` | `people`
  - **RESTRICTION**: `company` and `people` categories do NOT support `startPublishedDate`, `endPublishedDate`, or `excludeDomains`
- `objective`: string (up to 4096 chars) — the broader goal
- `systemPrompt`: string — instructions guiding output/behavior
- `outputSchema`: JSON schema (max 10 properties total, 2 levels nesting)
- `contents`: object with `highlights`, `text`, `summary`, `extras`
- `additionalQueries`: string[] (only for deep search types)
- `moderation`: boolean
- Response includes: `requestId`, `costDollars`, `searchTime`, `resolvedSearchType`

### Exa API Differences from Spec
- `snapshotAsOf` / historical snapshot: **NOT in current API** → UI will show "Snapshot research unavailable with current API"
- Monitors API: **excluded per user instruction** → not implemented

### Agent (`POST https://api.exa.ai/agent/runs`)
- `query` (required)
- `effort`: `minimal` | `low` | `medium` | `high` | `xhigh` | `auto` | `ultra`
- `outputSchema`: JSON schema
- `input.data`: array of objects for row enrichment
- `input.exclusion`: array of objects to exclude
- `systemPrompt`: string
- `stream`: boolean (SSE)
- `previousRunId`: for follow-up runs
- `dataSources`: Exa Connect integrations
- Async — poll via `GET https://api.exa.ai/agent/runs/{id}`
- Pricing: minimal $0.012, low $0.025, medium $0.10, high $0.50, xhigh $1.00, auto/ultra metered

## Architecture

```
React (Vite + TypeScript + Tailwind)
  ↓ TanStack Query
FastAPI (Python 3.12+)
  ↓
Research Orchestration
  ├── Exa Search Service
  └── Exa Agent Service
  ↓
SQLite (SQLAlchemy + Alembic)
```

## Backend Directory
```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── companies.py
│   │   ├── thesis.py
│   │   ├── signals.py
│   │   ├── search.py
│   │   ├── agent.py
│   │   ├── evidence.py
│   │   ├── entities.py
│   │   └── inbox.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/  (SQLAlchemy ORM)
│   ├── schemas/ (Pydantic v2)
│   ├── services/
│   │   ├── exa/
│   │   │   ├── client.py
│   │   │   ├── search.py
│   │   │   ├── agent.py
│   │   │   ├── normalization.py
│   │   │   ├── demo_search.py
│   │   │   └── demo_agent.py
│   │   ├── thesis_service.py
│   │   ├── signal_service.py
│   │   ├── evidence_service.py
│   │   └── inbox_service.py
│   └── db/
│       └── seed.py
├── tests/
├── requirements.txt
└── .env.example
```

## Frontend Directory
```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── thesis.ts
│   │   ├── signals.ts
│   │   ├── search.ts
│   │   ├── agent.ts
│   │   └── evidence.ts
│   ├── components/
│   │   ├── layout/
│   │   ├── thesis/
│   │   ├── signals/
│   │   ├── research/
│   │   ├── agent/
│   │   ├── evidence/
│   │   ├── inbox/
│   │   └── shared/
│   ├── pages/
│   │   ├── ThesisPage.tsx
│   │   ├── ResearchPage.tsx
│   │   ├── SignalsPage.tsx
│   │   └── InboxPage.tsx
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
```

## Implementation Phases
1. Backend foundation + database
2. Exa service layer
3. FastAPI routes
4. Frontend foundation + routing
5. Thesis + Signals UI
6. Research page (highest priority)
7. Agent + Enrichment + Inbox
8. Tests + README + polish
