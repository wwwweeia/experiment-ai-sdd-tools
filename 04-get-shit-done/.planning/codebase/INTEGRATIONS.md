---
title: External Integrations
last_mapped: 2026-05-18
---

# External Integrations

**Analysis Date:** 2026-05-18

## Databases

**Primary Database:**
- Type: SQLite (file-based, local)
- File location: `prompt_lab.db` (in project root)
- ORM: SQLAlchemy 2.0.36
- Connection: SQLite with `check_same_thread=False`
- Session management: FastAPI dependency injection via `get_db()` in `backend/app/core/database.py`

**Tables & Models:**
- `models` - LLM model configurations (id, name, provider, model_type, version, created_at)
- `prompts` - Prompt templates (id, title, content, variables, tags, created_by, created_at, updated_at)
- `agents` - AI agents (id, name, description, model_id, prompt_id, status, created_at)
- `skills` - Agent skills/tools (id, name, description, endpoint_url, agent_id, created_at)

**Schema Version:** Declarative ORM with type-hinted Mapped columns (SQLAlchemy 2.0 pattern)
- Auto-create on application startup: `Base.metadata.create_all(bind=engine)`
- Config file: `backend/app/core/config.py`
- Database module: `backend/app/core/database.py`

## External APIs

**No external APIs detected.**

This is a standalone application without integrations to:
- Third-party LLM APIs (OpenAI, Anthropic, etc.)
- Cloud services (AWS, Google Cloud, Azure)
- Analytics platforms
- Payment processors
- Email services

Note: The codebase has `Model` and `Prompt` entities that abstract LLM configuration, but the actual API calls to external LLM providers are **not implemented** in this project.

## Authentication & Authorization

**Current State:** Not detected

**No auth provider configured** in the codebase:
- No OAuth2 flows
- No JWT token handling
- No session management
- No user authentication

**CORS Configuration:**
- Backend: `CORSMiddleware` in `backend/app/main.py`
  - `allow_origins`: `["http://localhost:5173"]` (frontend only)
  - `allow_credentials`: `True`
  - `allow_methods`: `["*"]`
  - `allow_headers`: `["*"]`
- This enables same-origin requests from frontend to backend during development

## Data Storage

**Local File Storage:**
- No dedicated file storage service
- SQLite database is the only persistent storage

**In-Memory State:**
- Pinia store (`backend` N/A, frontend uses `src/stores/`)
  - `prompt.js` - Prompt list state
  - Additional stores can be added for other entities

## Caching

**Not detected.**

No caching layer is configured:
- No Redis
- No Memcached
- No application-level caching

Database queries run directly against SQLite without caching.

## Monitoring & Observability

**Health Check Endpoint:**
- `GET /health` - Returns `{"status": "ok", "service": "AI Prompt Lab", "version": "1.0.0"}`
- Location: `backend/app/main.py`

**Logging:**
- Not configured (would use Python's logging module if added)
- No external logging service integration detected

**Error Tracking:**
- Frontend: ElMessage from Element Plus for user-facing errors
  - Response interceptor in `frontend/src/api/index.js` catches and displays errors
- Backend: HTTPException for API errors
  - 404 responses for missing resources
  - FastAPI auto-documents errors in `/docs` (Swagger UI)

**Performance Monitoring:**
- Not detected
- No APM (Application Performance Monitoring) tools configured

## Webhooks & Callbacks

**Not implemented.**

No webhook endpoints or external callbacks are configured:
- No incoming webhooks from external services
- No outgoing webhooks to other systems

**Potential Future Use:**
- `Skill.endpoint_url` field suggests skills may eventually be external HTTP endpoints
- Currently stored but not called

## Environment Configuration

**Required Environment Variables:**
- None currently enforced

**Optional/Future:**
- `E2E_BASE_URL` - E2E test frontend URL (defaults to `http://localhost:5173`)
- `E2E_HEADLESS` - E2E browser mode (defaults to `true`)
- `CI` - CI environment indicator (used by Playwright for retries)

**Secrets:**
- No secrets management detected (.env files not used)
- SQLite database is local and file-based (no credentials needed for development)

**Configuration Files:**
- Backend: `backend/app/core/config.py`
- Frontend: `frontend/vite.config.js`
- E2E: `e2e/playwright.config.ts`

## API Clients

**Frontend HTTP Client:**
- Axios 1.7.0
  - Base timeout: 10 seconds
  - Location: `frontend/src/api/index.js`
  - Response interceptor validates `response.data.code === 0`
  - Auto-extracts `response.data` (unwraps Response wrapper)
  - Error handling: ElMessage notifications

**API Modules:**
- `frontend/src/api/prompts.js` - Prompt CRUD endpoints
  - Methods: `fetchPrompts()`, `fetchPrompt(id)`, `createPrompt(data)`, `deletePrompt(id)`
  - No agents API client yet (to be implemented)

**Backend API:**
- FastAPI automatic OpenAPI documentation at `/docs` (Swagger UI)
- API version: v1 (prefix: `/api/v1`)
- Response format: Generic `Response[T]` wrapper with `code`, `data`, `message` fields

## Deployment Infrastructure

**Not configured for production.**

Development setup:
- Backend: Uvicorn ASGI server (development mode with auto-reload)
- Frontend: Vite dev server (with hot module replacement)
- Proxy: Vite dev server proxies `/api/*` to `http://localhost:8000`

**No CI/CD pipeline detected:**
- No GitHub Actions
- No GitLab CI
- No other automation

**No container configuration:**
- No Docker/Docker Compose
- No Kubernetes manifests

---

*Integration audit: 2026-05-18*
