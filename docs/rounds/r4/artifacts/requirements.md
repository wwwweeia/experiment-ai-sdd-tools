<!-- 此文件由 docs:collect 自动生成，源：04-get-shit-done/.planning/REQUIREMENTS.md。请编辑源文件而非本文件。 -->

# Requirements: AI Prompt Lab — Agent 状态管理

**Defined:** 2026-05-18
**Core Value:** Agent 能够被安全地激活和停用——激活时确保 Model + Prompt 依赖就绪，停用时有完整记录，状态管理对前端透明可操作。

## v1 Requirements

### Agent CRUD

- [ ] **AGENT-01**: 用户可以获取 Agent 列表（支持分页、按状态筛选：全部/DRAFT/ACTIVE/INACTIVE）
- [ ] **AGENT-02**: 用户可以获取单个 Agent 详情（含关联 Model 和 Prompt 名称）
- [ ] **AGENT-03**: 用户可以创建 Agent（指定名称、描述、model_id、prompt_id；初始状态固定为 DRAFT）
- [ ] **AGENT-04**: 用户可以删除 DRAFT 或 INACTIVE 状态的 Agent；ACTIVE Agent 删除时返回错误提示

### 状态机

- [ ] **STATE-01**: 用户可以切换 Agent 状态（PATCH /agents/{id}/status），系统执行转换规则验证：
  - 有效转换：DRAFT → ACTIVE，ACTIVE → INACTIVE，INACTIVE → ACTIVE
  - 激活前置：model_id 和 prompt_id 必须存在且关联记录有效
  - 无效转换返回 409；前置条件不满足返回 422 含具体原因
- [ ] **STATE-02**: 每次状态变更自动写入 AgentStatusHistory 记录（含 from_status、to_status、reason、changed_at）

### 前端

- [ ] **FRONT-01**: Agent 列表页显示名称、状态标签、关联 Model 名称、关联 Prompt 名称，支持状态筛选和分页
- [ ] **FRONT-02**: 每行操作按钮按状态显示（DRAFT→激活；ACTIVE→停用；INACTIVE→激活+删除），点击后弹出确认对话框，失败时展示具体原因
- [ ] **FRONT-03**: 创建 Agent 表单含名称（必填）、描述（选填）、Model 下拉选择（懒加载）、Prompt 下拉选择（懒加载）

## v2 Requirements

### 状态历史

- **HIST-01**: 前端展示 Agent 状态变更历史时间线
- **HIST-02**: GET /agents/{id}/history 独立历史查询端点

### 增强功能

- **ENHA-01**: 批量状态操作（多选 Agent 批量激活/停用）
- **ENHA-02**: Agent 列表状态变更实时轮询
- **ENHA-03**: 停用时在确认对话框中展示关联 Skill 影响预览

## Out of Scope

| Feature | Reason |
|---------|--------|
| Skill.is_active 字段 | 停用意图已通过 Agent.status 完整表达，避免引入冗余状态同步 |
| 认证 / 鉴权 | 实验项目，不在本次范围 |
| 前端单元测试 | 手动验证 + 后端 pytest 覆盖业务规则，前端 E2E 为可选 |
| Skill 管理页面 | 聚焦 Agent 状态管理 |
| Mobile 适配 | Web-first |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGENT-01 | Phase 1 | Pending |
| AGENT-02 | Phase 1 | Pending |
| AGENT-03 | Phase 1 | Pending |
| AGENT-04 | Phase 1 | Pending |
| STATE-01 | Phase 1 | Pending |
| STATE-02 | Phase 1 | Pending |
| FRONT-01 | Phase 2 | Pending |
| FRONT-02 | Phase 2 | Pending |
| FRONT-03 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-18*
*Last updated: 2026-05-18 after initial definition*
