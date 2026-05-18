---
title: Directory Structure
last_mapped: 2026-05-18
---

# Directory Structure

## Top-Level Layout

```
04-get-shit-done/
├── backend/                  # FastAPI Python backend
├── frontend/                 # Vue 3 SPA frontend
├── e2e/                      # Playwright E2E tests
├── .claude/                  # Claude Code + GSD commands & agents
│   ├── commands/gsd/         # GSD slash command definitions
│   ├── agents/               # GSD sub-agent definitions
│   └── get-shit-done/        # GSD workflow markdown files
├── .planning/                # GSD planning artifacts (generated)
│   └── codebase/             # Codebase map documents (this folder)
└── CLAUDE.md                 # Project instructions for Claude
```

## Backend Structure

```
backend/
├── requirements.txt          # Python dependencies
├── scripts/
│   └── seed.py               # Database seeding script
└── app/
    ├── main.py               # FastAPI app entry point
    ├── core/
    │   ├── config.py         # PROJECT_NAME, VERSION, API_PREFIX constants
    │   └── database.py       # SQLite engine, SessionLocal, get_db()
    ├── models/
    │   └── entity.py         # ALL ORM models: Model, Prompt, Agent, Skill, AgentStatus
    ├── schemas/
    │   └── schema.py         # ALL Pydantic schemas + Response[T] wrapper
    ├── services/
    │   ├── model_service.py  # ModelService — CRUD for Model entity
    │   └── prompt_service.py # PromptService — CRUD for Prompt entity
    └── api/v1/
        ├── endpoints.py      # ALL route handlers (models_router, prompts_router)
        └── router.py         # Aggregates routers → /api/v1/models, /api/v1/prompts
```

## Frontend Structure

```
frontend/
├── index.html                # HTML entry
├── package.json              # npm dependencies
└── src/
    ├── main.js               # Vue app init (registers Element Plus, Pinia, Router)
    ├── App.vue               # Root component with <router-view>
    ├── api/
    │   ├── index.js          # Axios instance + response interceptor
    │   └── prompts.js        # Prompt API functions (reference pattern)
    ├── stores/
    │   ├── prompt.js         # Prompt Pinia store (reference pattern)
    │   └── agent.js          # Agent Pinia store (stub — needs implementation)
    ├── views/
    │   ├── Home.vue          # Dashboard with entity count stats
    │   ├── PromptList.vue    # Full CRUD page (reference pattern)
    │   └── AgentList.vue     # Agent list placeholder (15 lines — needs implementation)
    └── router/
        └── index.js          # Routes: / → Home, /prompts → PromptList, /agents → AgentList
```

## E2E Structure

```
e2e/
├── package.json
├── playwright.config.ts      # Playwright config (baseURL, headless, retries)
├── pages/
│   ├── base.page.ts          # BasePage base class with shared helpers
│   ├── home.page.ts          # HomePage page object
│   └── prompt-list.page.ts   # PromptListPage page object
└── tests/
    ├── home.spec.ts           # Home page tests
    └── prompt-list.spec.ts    # Prompt list CRUD tests
```

## Key Locations

| What | Where |
|------|-------|
| FastAPI entry | `backend/app/main.py` |
| Database config | `backend/app/core/database.py` |
| All ORM models | `backend/app/models/entity.py` |
| All Pydantic schemas | `backend/app/schemas/schema.py` |
| Response wrapper `Response[T]` | `backend/app/schemas/schema.py` |
| Service pattern reference | `backend/app/services/prompt_service.py` |
| API endpoint pattern reference | `backend/app/api/v1/endpoints.py` |
| Route registration | `backend/app/api/v1/router.py` |
| Axios setup + interceptor | `frontend/src/api/index.js` |
| API client pattern reference | `frontend/src/api/prompts.js` |
| Pinia store pattern reference | `frontend/src/stores/prompt.js` |
| Vue page pattern reference | `frontend/src/views/PromptList.vue` |
| Client-side routing | `frontend/src/router/index.js` |

## Naming Conventions

### Backend Files
- Services: `{entity}_service.py` (e.g., `model_service.py`)
- All models in one file: `entity.py`
- All schemas in one file: `schema.py`
- All endpoints in one file: `endpoints.py`

### Frontend Files
- Views: `{EntityName}List.vue`, `{EntityName}Detail.vue` (PascalCase)
- Stores: `{entity}.js` (camelCase, no "store" suffix in filename)
- API modules: `{entity}s.js` (plural camelCase)

### URL Patterns
- API prefix: `/api/v1/{resource}s/` (plural, trailing slash)
- Status update: `/api/v1/{resource}s/{id}/status`
- Frontend routes: `/{resource}s` (plural, no trailing slash)
