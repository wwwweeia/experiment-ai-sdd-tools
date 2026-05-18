---
phase: 01-backend
plan: 01
subsystem: database
tags: [sqlalchemy, pydantic, state-machine, audit-log, orm]

# Dependency graph
requires: []
provides:
  - AgentStatusHistory ORM table (append-only audit log for Agent state changes)
  - Agent.status_history back-relationship with cascade delete-orphan
  - AgentCreate schema without status field (DRAFT enforced at ORM level)
  - AgentRead schema with AgentStatus enum and model_name/prompt_name slots
  - StatusChangeRequest schema (typed target state + optional reason)
  - StatusHistoryRead schema (audit row read representation)
affects:
  - 01-02 (AgentService depends on these models/schemas)
  - 01-03 (API endpoints depend on AgentRead, StatusChangeRequest)
  - 01-04 (Tests depend on all schemas and AgentStatusHistory)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Python-side datetime.now default (consistent with existing ORM pattern, not server_default)
    - AgentStatus enum typed directly in Pydantic schemas (not str)
    - ConfigDict(use_enum_values=True) for enum serialization to lowercase strings

key-files:
  created: []
  modified:
    - backend/app/models/entity.py
    - backend/app/schemas/schema.py

key-decisions:
  - "Use Python-side default=datetime.now for changed_at (consistent with existing ORM pattern; RESEARCH.md server_default overridden by codebase convention)"
  - "Prompt.title (not .name) is the source for AgentRead.prompt_name — preserved from interface spec"
  - "StatusHistoryRead provisioned now for downstream use in Plan 04 tests even though no history endpoint exists in this plan"

patterns-established:
  - "All new ORM classes follow Mapped[T] = mapped_column(...) pattern with type annotations"
  - "Schema import pattern: from app.models.entity import AgentStatus (not redefinition)"

requirements-completed:
  - AGENT-01
  - AGENT-02
  - AGENT-03
  - STATE-02

# Metrics
duration: 2min
completed: 2026-05-18
---

# Phase 01 Plan 01: Data Layer Foundation Summary

**AgentStatusHistory append-only audit table + Agent schema surgery — AgentCreate locks to DRAFT, AgentRead gains enum status and relation-name slots, two new typed request/response schemas added**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-18T10:40:18Z
- **Completed:** 2026-05-18T10:41:52Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `AgentStatusHistory` ORM class created with 6 columns (id, agent_id with CASCADE FK, from_status nullable enum, to_status non-null enum, reason String(500), changed_at Python-side default) and `agent_status_history` table confirmed created in SQLite
- `Agent.status_history` back-relationship added with `cascade="all, delete-orphan"` ordered by `changed_at`
- `AgentCreate` purged of `status` field — clients can no longer set initial status (AGENT-03 enforced at schema boundary)
- `AgentRead` upgraded: `status` from `str` to `AgentStatus` enum with `use_enum_values=True`, plus `model_name`/`prompt_name` slots for service-layer eager-load
- `StatusChangeRequest` and `StatusHistoryRead` schemas provisioned for downstream service and test plans

## Task Commits

Each task was committed atomically:

1. **Task 1: Add AgentStatusHistory ORM table and status_history relationship** - `f0badef` (feat)
2. **Task 2: Fix AgentCreate/AgentRead schemas and add StatusChangeRequest + StatusHistoryRead** - `21609ea` (feat)

## Files Created/Modified
- `backend/app/models/entity.py` — Added `AgentStatusHistory(Base)` class (lines 75-93) and `status_history` relationship on `Agent` (lines 59-61)
- `backend/app/schemas/schema.py` — Added `AgentStatus` import, replaced `AgentCreate` and `AgentRead`, added `StatusChangeRequest` and `StatusHistoryRead`

## Decisions Made
- Used `default=datetime.now` (Python-side) for `changed_at` instead of `server_default=func.now()` — consistent with all existing `created_at` patterns in the codebase (SQLite portability; RESEARCH.md reference overridden by convention)
- `prompt_name` sourced from `agent.prompt.title` (not `.name`) — `Prompt` model uses `title` field, preserved from interface spec in plan
- `StatusHistoryRead` provisioned proactively for Plan 04 tests even though no GET history endpoint is created in this plan

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Data layer fully ready for Plan 02 (AgentService business logic)
- All schema contracts established: `AgentCreate`, `AgentRead`, `StatusChangeRequest`, `StatusHistoryRead`
- `AgentStatusHistory` table auto-created in SQLite on next app startup (idempotent via `Base.metadata.create_all`)
- No blockers — Plan 02 can proceed immediately

---
*Phase: 01-backend*
*Completed: 2026-05-18*
