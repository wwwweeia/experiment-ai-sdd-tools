<!--
Sync Impact Report
==================
Version change: N/A → 1.0.0 (initial ratification)
Modified principles: N/A (first version)
Added sections:
  - Core Principles (5 principles)
  - Technology Constraints
  - Development Workflow
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ compatible (Constitution Check gate present)
  - .specify/templates/spec-template.md: ✅ compatible (user stories & requirements align)
  - .specify/templates/tasks-template.md: ✅ compatible (phase structure aligns)
  - .specify/templates/commands/: N/A (directory does not exist)
Follow-up TODOs: None
-->

# AI Prompt Lab Constitution

## Core Principles

### I. API-First Design

All features MUST start with a well-defined REST API endpoint. Backend APIs
drive the entire system; the frontend is a consumer. Every new capability
begins with designing the API contract (endpoint, request/response schema,
error codes) before any implementation.

- API endpoints MUST follow RESTful conventions under `/api/v1/`
- Every endpoint MUST have a corresponding Pydantic schema for validation
- API design documents MUST be reviewed before implementation begins

### II. Entity Relationship Integrity

The four core entities (Model, Prompt, Agent, Skill) have strict
relationships that MUST be enforced at both database and API levels.

- Agent MUST be associated with a Model and a Prompt before it can transition
  to ACTIVE state
- Agent lifecycle MUST follow the state machine: DRAFT → ACTIVE → INACTIVE
  (no skipping states, no reverse transitions except INACTIVE → DRAFT)
- All foreign key constraints MUST be enforced; deleting a Model or Prompt
  that is bound to an ACTIVE Agent MUST be rejected

### III. Consistent API Contract

All API responses MUST follow a uniform envelope format, regardless of
success or failure.

- Success response: `{"code": 0, "data": <payload>, "message": "ok"}`
- Error response: `{"code": <non-zero>, "data": null, "message": "<description>"}`
- List endpoints MUST return paginated results with metadata
- HTTP status codes MUST accurately reflect the outcome (200, 201, 400, 404,
  422, 500)

### IV. Full-Stack Synchronization

Backend and frontend changes MUST be delivered together for any given feature.
A backend-only or frontend-only change is acceptable only for bug fixes or
refactoring.

- New API endpoints MUST include corresponding frontend integration
- Frontend stores (Pinia) MUST mirror backend data models
- Breaking API changes MUST include frontend migration in the same delivery

### V. Simplicity & Iteration

Start with the simplest viable implementation. SQLite is the default storage
for development. Premature optimization, over-engineering, and speculative
abstractions are prohibited.

- YAGNI: do not build for hypothetical future requirements
- SQLite for local/dev; database migration path documented but not pre-built
- Three similar lines of code are better than a premature abstraction
- Each feature increment MUST be independently deployable and testable

## Technology Constraints

**Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite
(local development)

**Frontend**: Vue 3 (Composition API), Element Plus, Pinia, Vite

**Testing**: Playwright E2E tests for critical user journeys; pytest for
backend unit/integration tests when needed

**Project Structure**: Monorepo with `backend/`, `frontend/`, and `e2e/`
directories

**Package Management**: pip (backend), npm (frontend/e2e)

## Development Workflow

1. **Feature Specification**: Write spec → clarify → plan → tasks
2. **Implementation Order**: API schema → API endpoint → service layer →
   frontend store → frontend view → E2E test
3. **Commit Discipline**: Commit after each logical unit of work; use
   conventional commit messages (`feat:`, `fix:`, `refactor:`, `docs:`)
4. **Testing**: E2E tests cover critical paths; manual verification for UI
   changes before marking complete
5. **Review**: Self-review code for OWASP top 10 vulnerabilities before
   committing; no security shortcuts

## Governance

This constitution is the authoritative source for development principles and
constraints. All specifications, plans, and implementation decisions MUST
comply with these principles.

- **Amendment Procedure**: Any principle change requires updating this
  document with version bump and sync impact report
- **Versioning**: MAJOR for principle removal/redefinition, MINOR for new
  principles or expanded guidance, PATCH for clarifications and wording fixes
- **Compliance**: Every implementation plan MUST include a Constitution Check
  gate; violations MUST be documented with justification in the Complexity
  Tracking section
- **Runtime Guidance**: CLAUDE.md provides project-specific context and
  supplements this constitution with practical instructions

**Version**: 1.0.0 | **Ratified**: 2026-05-13 | **Last Amended**: 2026-05-13
