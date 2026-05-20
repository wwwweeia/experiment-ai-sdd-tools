# 状态机实现对比

> 同一功能最核心的差异。四个工具给出了四种状态机实现（R3 和 R4 同为映射表，但错误语义处理不同）。

## Round 1（Superpowers）— 元组集合

```python
ALLOWED_TRANSITIONS = {
    (AgentStatus.DRAFT, AgentStatus.ACTIVE),
    (AgentStatus.ACTIVE, AgentStatus.INACTIVE),
    (AgentStatus.INACTIVE, AgentStatus.ACTIVE),
}

# 校验：元组查找
if (agent.status, target) not in ALLOWED_TRANSITIONS:
    raise HTTPException(422, ...)
```

- 优点：扁平、无歧义
- 缺点：查找是 O(n) 遍历（3 个元素无所谓），没有声明"从某状态可以到哪些状态"
- **额外加分**：Service 层直接抛 HTTPException（与 FastAPI 深度耦合，但简洁）

## Round 2（Spec-Kit）— if/elif 分支

```python
def activate_agent(self, agent_id: int) -> Agent:
    agent = self.get_agent(agent_id)
    if not agent:
        raise ValueError("Agent not found")
    if agent.status == AgentStatus.ACTIVE:
        raise ValueError("Agent 已是 ACTIVE 状态")
    if agent.status == AgentStatus.INACTIVE and False:  # 死代码
        pass
    # ... 校验逻辑

def deactivate_agent(self, agent_id: int) -> Agent:
    if agent.status != AgentStatus.ACTIVE:
        raise ValueError("只有 ACTIVE 状态的 Agent 可以停用")
```

- 激活和停用各一个方法，状态判断分散在两个函数中
- 缺点：状态机逻辑不集中，新增状态需要改多处
- **有死代码**：`if agent.status == AgentStatus.INACTIVE and False: pass`

## Round 3（OpenSpec）— 映射表

```python
TRANSITIONS = {
    AgentStatus.DRAFT: {AgentStatus.ACTIVE},
    AgentStatus.ACTIVE: {AgentStatus.INACTIVE},
    AgentStatus.INACTIVE: {AgentStatus.ACTIVE},
}

# 校验：集合查找
if target_status not in self.TRANSITIONS.get(current, set()):
    allowed = [s.value for s in self.TRANSITIONS.get(current, set())]
    return None, f"不允许从 {current.value} 转换到 {target_status.value}，允许的目标状态: {allowed}"
```

- 优点：声明式、O(1) 查找、易扩展、错误消息自动包含允许的目标状态
- **最佳设计**：三个版本中最优雅的状态机实现

## Round 4（GSD）— 映射表（列表值）+ 独立异常类

```python
VALID_TRANSITIONS: dict[AgentStatus, list[AgentStatus]] = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

# 校验：列表查找 + 双异常路径
allowed = VALID_TRANSITIONS.get(old_status, [])
if data.status not in allowed:
    raise InvalidTransitionError(old_status, data.status)  # → 409
if data.status == AgentStatus.ACTIVE:
    self._assert_activation_ready(agent)                    # → 422
```

- 结构同 Round 3，但明确区分了"非法转换（409 Conflict）"和"激活前置失败（422 Unprocessable）"两种错误语义
- 独立异常类 `InvalidTransitionError` / `ActivationNotReadyError`，API 层精确映射 HTTP 状态码

## 评判

**Round 3 ≈ Round 4 > Round 1 > Round 2**。GSD 和 OpenSpec 都用了映射表，GSD 额外做了异常语义分离（更工程化），OpenSpec 的错误收集设计更用户友好。

| 维度 | R1 元组集合 | R2 if/elif | R3 映射表 | R4 映射表+独立异常 |
|------|------------|-----------|----------|-----------------|
| 可读性 | 中 | 低（逻辑分散） | **高**（声明式） | **高**（声明式） |
| 可扩展性 | 中（加元组） | 低（改多处） | **高**（加 key 即可） | **高**（加 key 即可） |
| 查找复杂度 | O(n) | O(条件数) | **O(1)** | **O(1)** |
| 错误信息质量 | 中 | 中 | **高**（自动列允许目标） | **高**（同R3）+ 错误语义精确 |
| 与 Web 框架耦合 | 高（抛 HTTPException） | 低（抛 ValueError） | 低（返回 tuple） | 低（独立异常类） |
