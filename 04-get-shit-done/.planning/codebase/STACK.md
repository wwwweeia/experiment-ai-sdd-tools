---
title: Tech Stack
last_mapped: 2026-05-18
---

# Tech Stack

**Analysis Date:** 2026-05-18

## Languages

**Backend:**
- Python 3.13.9 - FastAPI backend application

**Frontend:**
- JavaScript (ES Module) - Vue 3 SPA application
- TypeScript 5.8 - E2E testing (Playwright)

## Runtime & Build

**Backend:**
- Python 3.13.9 (local development)
- Uvicorn 0.34.0 - ASGI server with `uvicorn[standard]` extras
- Development: `uvicorn app.main:app --reload`

**Frontend:**
- Node.js v22.22.2 (verified)
- Vite 6.0.0 - Build tool and dev server
- Dev server: `npm run dev` (runs on http://localhost:5173)
- Build: `npm run build` (production bundle)
- Preview: `npm run preview` (serve built assets)

## Frameworks

**Backend:**
- FastAPI 0.115.6 - Web framework
  - Project name: "AI Prompt Lab"
  - Version: 1.0.0
  - API prefix: `/api/v1`
  - CORS enabled for `http://localhost:5173`

**Frontend:**
- Vue 3.5.0 - SPA framework (Composition API)
- Vue Router 4.4.0 - Client-side routing
- Pinia 2.2.0 - State management store
- Element Plus 2.9.0 - UI component library
  - CSS bundled from `element-plus/dist/index.css`

**Testing:**
- Playwright 1.52.0 (@playwright/test) - E2E testing framework
  - Browser: Desktop Chrome
  - Config: `e2e/playwright.config.ts`
  - Execution: Single worker, no parallel tests
  - HTML report generation
  - Screenshot/video on failure

## Key Dependencies

**Backend (Core):**
- SQLAlchemy 2.0.36 - ORM for database operations
  - Declarative base pattern
  - Mapped columns with type hints
  - Foreign key relationships (Model → Agent, Prompt → Agent, Agent → Skill)
  - SQLite backend with auto-table creation
- Pydantic 2.10.4 - Data validation and serialization
  - Generic response wrapper `Response[T]`
  - Schema models with `ConfigDict(from_attributes=True)`

**Frontend (Core):**
- Axios 1.7.0 - HTTP client
  - Base timeout: 10 seconds
  - Response interceptor for unified error handling
  - Auto-unwraps `response.data` and validates `code === 0`
- Sass/SCSS (sass-embedded 1.80.0) - CSS preprocessing

**Development:**
- @vitejs/plugin-vue 5.2.0 - Vue 3 Vite integration
- @types/node 22.0.0 - TypeScript node types (E2E)

## Configuration

**Backend:**
- Location: `backend/app/core/config.py`
- `PROJECT_NAME`: "AI Prompt Lab"
- `VERSION`: "1.0.0"
- `API_PREFIX`: "/api/v1"
- `DATABASE_URL`: SQLite at `prompt_lab.db` (root of backend directory)

**Frontend:**
- Vite config: `frontend/vite.config.js`
- Entry point: `frontend/index.html`
- Mount: `<div id="app"></div>`
- Proxy: `/api/*` → `http://localhost:8000`
- Port: 5173

**Database:**
- Type: SQLite (file-based)
- Path: `{project_root}/prompt_lab.db`
- Auto-created on startup via `Base.metadata.create_all(bind=engine)`
- Configuration: `backend/app/core/database.py`
  - Engine: SQLite with `check_same_thread=False`
  - SessionLocal: sessionmaker with autocommit/autoflush disabled
  - Session dependency: FastAPI `Depends(get_db)`

**E2E Testing:**
- Config: `e2e/playwright.config.ts`
- Test directory: `e2e/tests/`
- Test files: `*.spec.ts`
- Base URL: `http://localhost:5173` (configurable via `E2E_BASE_URL` env var)
- Headless mode: Enabled by default (configurable via `E2E_HEADLESS` env var)
- Timeout: 30 seconds per test, 5 seconds per assertion
- CI configuration: Retry 2 times on CI, single worker

**Development Tools:**
- CORS: Enabled for localhost:5173 on FastAPI app
- Health check endpoint: `GET /health` (returns status, service name, version)

## Package Management

**Backend:**
- Package Manager: pip
- Lock file: N/A (requirements.txt with pinned versions)
- Dependency location: `backend/requirements.txt`

**Frontend:**
- Package Manager: npm
- Lock file: `frontend/package-lock.json` (present)
- Dependency location: `frontend/package.json`
- Workspace: None (single root)

**E2E:**
- Package Manager: npm
- Lock file: `e2e/package-lock.json` (present)
- Dependency location: `e2e/package.json`
- Separate from frontend dependencies

## Platform Requirements

**Development:**
- Python 3.13.9+
- Node.js v22+ (verified v22.22.2)
- npm (comes with Node)
- Bash/shell for running startup scripts

**Production:**
- Python runtime (FastAPI + Uvicorn)
- Web server (Nginx/Apache to reverse proxy Uvicorn)
- Node.js build environment (for frontend build step)
- SQLite support (included in Python stdlib)

---

*Stack analysis: 2026-05-18*
