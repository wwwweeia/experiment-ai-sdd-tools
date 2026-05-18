# Stack Research

**Domain:** FastAPI + SQLAlchemy 2.x state machine — Agent lifecycle management (DRAFT/ACTIVE/INACTIVE)
**Researched:** 2026-05-18
**Confidence:** HIGH

## Recommended Stack

### Core Technologies (Already Installed — No New Dependencies)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.115.6 | HTTP layer, route handling for PATCH /agents/{id}/status | Already in requirements.txt; native Pydantic v2 integration; status code control via HTTPException |
| SQLAlchemy | 2.0.36 | ORM for Agent/AgentStatusHistory models | Already in requirements.txt; mapped_column + Mapped[] type hints already in use; Session.execute + select() pattern established |
| Pydantic | 2.10.4 | Request/response schema validation for status transition payload | Already in requirements.txt; AgentCreate/AgentRead already defined; v2 model_config = ConfigDict(from_attributes=True) pattern in place |

### State Machine Implementation: Pure Python (Recommended)

**Decision: Do NOT add python-statemachine or transitions library.**

The constraint in PROJECT.md is explicit: "不引入新依赖". More importantly, with only 3 states and 4 valid transitions, a library adds overhead without benefit:

```
DRAFT   → ACTIVE    (requires: model_id not None, prompt_id not None, both records exist)
ACTIVE  → INACTIVE  (always allowed)
INACTIVE → ACTIVE   (requires: model_id not None, prompt_id not None, both records still exist)
DRAFT   → DELETE    (guard: status must be DRAFT or INACTIVE)
ACTIVE  → DELETE    (blocked: raise HTTPException 409)
```

Implement as a TRANSITIONS dict + guard methods inside AgentService:

```python
# Pure Python state machine — no library needed
VALID_TRANSITIONS: dict[tuple[AgentStatus, AgentStatus], bool] = {
    (AgentStatus.DRAFT, AgentStatus.ACTIVE): True,
    (AgentStatus.ACTIVE, AgentStatus.INACTIVE): True,
    (AgentStatus.INACTIVE, AgentStatus.ACTIVE): True,
}

def _check_activation_guards(self, agent: Agent) -> None:
    """Guard for DRAFT→ACTIVE and INACTIVE→ACTIVE: Model and Prompt must exist."""
    if not agent.model_id or not agent.prompt_id:
        raise HTTPException(400, "Agent must have a model and prompt before activation")
    model = self.db.get(Model, agent.model_id)
    prompt = self.db.get(Prompt, agent.prompt_id)
    if not model:
        raise HTTPException(400, f"Associated model {agent.model_id} no longer exists")
    if not prompt:
        raise HTTPException(400, f"Associated prompt {agent.prompt_id} no longer exists")
```

This pattern was used in R3 (OpenSpec) and rated the best design decision of the three rounds.

### State Change History: Separate Table (Recommended)

**Decision: Separate `agent_status_history` table, NOT a JSON column on Agent.**

Rationale:
- JSON column on Agent requires deserializing the whole history array for every read — wasteful and unindexable
- Separate table gives clean foreign key, queryable `changed_at` timestamps, and aligns with PROJECT.md requirement "记录变更时间和原因"
- SQLite handles multi-table writes in a single transaction fine
- Schema is append-only: one INSERT per transition, no UPDATE complexity

```python
class AgentStatusHistory(Base):
    __tablename__ = "agent_status_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    from_status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), nullable=False)
    to_status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    agent: Mapped["Agent"] = relationship(back_populates="status_histories")
```

Write the history row in the same `db.commit()` as the Agent status update — atomic, consistent.

### Supporting Libraries (None New — Use Existing Patterns)

| Pattern | Implementation | Why |
|---------|---------------|-----|
| Eager loading for Agent detail | `selectinload(Agent.model)` + `selectinload(Agent.prompt)` | Avoids N+1 on list endpoint; SQLAlchemy 2.x select() + options() pattern |
| Status filtering on list | `where(Agent.status == status_filter)` | Native SQLAlchemy; status is already an Enum column |
| Pagination | `offset(skip).limit(limit)` | Matches existing PromptService pattern exactly |

## Installation

No new packages required. The full stack is already installed:

```bash
# Already in backend/requirements.txt:
# fastapi==0.115.6
# sqlalchemy==2.0.36
# pydantic==2.10.4
# uvicorn[standard]==0.34.0
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Pure Python TRANSITIONS dict | python-statemachine 3.1.1 | Use if state count >10, complex guards with callbacks, diagram generation needed |
| Pure Python TRANSITIONS dict | transitions (pytransitions) | Use if hierarchical/nested states required (HSM support) |
| Separate history table | JSON column on Agent.status_history | Use only if schema changes are frequent and you can't afford migrations |
| Separate history table | SQLAlchemy `@event.listens_for` on `after_bulk_update` | Viable but couples audit to ORM internals; harder to reason about |
| `db.get(Model, id)` for guard checks | `joinedload` on Agent | joinedload is fine for detail views, but guard checks need lazy-loadable per-check control |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `sqlalchemy-fsm` (presslabs) | Last release August 2022; no SQLAlchemy 2.x support confirmed; 5 stars, essentially unmaintained | Pure Python TRANSITIONS dict |
| `sqlalchemy-state-machine` | PyPI advisory: discontinued, no releases in 12+ months | Pure Python TRANSITIONS dict |
| `state_machine` (jtushman) | Targets SQLAlchemy 1.x, last active ~2018 | Pure Python TRANSITIONS dict |
| Legacy `Session.query()` API | Already not used in this codebase; SQLAlchemy 2.x deprecates it | `Session.execute(select(...))` — already the pattern in place |
| `db.query(Prompt).filter(...)` in new AgentService | Inconsistency risk; PromptService uses legacy query but AgentService should use 2.x style | `db.execute(select(Agent).where(...)).scalars()` |

**Note on PromptService:** It uses the legacy `db.query()` API (line 11: `query = self.db.query(Prompt)`). This is still supported in SQLAlchemy 2.x but is deprecated for removal in 3.0. New AgentService should use `select()` style to be forward-compatible.

## Stack Patterns by Context

**For the status transition endpoint (PATCH /agents/{id}/status):**
- Input schema: `AgentStatusUpdate(target_status: AgentStatus, reason: str | None)`
- Validate transition in AgentService via VALID_TRANSITIONS dict
- Run guard function only when target is ACTIVE
- Write Agent.status update + AgentStatusHistory row in single commit
- Return `Response[AgentRead]` — consistent with all other endpoints

**For the Agent list endpoint (GET /agents/):**
- Support `status: AgentStatus | None = None` query param for filtering
- Use `selectinload` on model and prompt relationships for joined names in response
- Extend `AgentRead` schema to include `model_name: str | None` and `prompt_name: str | None`

**For the delete guard:**
- Check `agent.status == AgentStatus.ACTIVE` before deleting
- Raise `HTTPException(409, "Cannot delete an active agent. Deactivate it first.")` — 409 Conflict is semantically correct

## Version Compatibility

| Package | Version | Compatibility Notes |
|---------|---------|---------------------|
| SQLAlchemy 2.0.36 | FastAPI 0.115.6 | Fully compatible; `get_db` dependency pattern already working |
| Pydantic 2.10.4 | SQLAlchemy 2.0.36 | `model_config = ConfigDict(from_attributes=True)` required on all Read schemas — already the pattern |
| Python 3.9+ | python-statemachine 3.1.1 | Would be compatible IF added, but not needed |
| SQLite | AgentStatusHistory table | SQLite supports multi-table foreign keys and transactions; no issue for this scale |

## Sources

- PyPI python-statemachine — version 3.1.1 released 2026-05-18, confirmed active maintenance (HIGH confidence)
- Context7 /fgmacedo/python-statemachine — guards, MachineMixin, Django integration patterns fetched (HIGH confidence)
- PyPI sqlalchemy-fsm — last release August 2022, effectively unmaintained (HIGH confidence)
- PyPI sqlalchemy-state-machine — Snyk advisory: discontinued (HIGH confidence)
- PROJECT.md constraint "不引入新依赖" — decisive factor for pure Python recommendation
- R3 (OpenSpec) post-round notes — TRANSITIONS dict pattern rated best design decision across 3 rounds (MEDIUM confidence, internal experiment data)
- SQLAlchemy 2.x official docs — `Session.execute + select()` is the current canonical API (HIGH confidence)

---
*Stack research for: FastAPI + SQLAlchemy 2.x state machine / Agent lifecycle management*
*Researched: 2026-05-18*
