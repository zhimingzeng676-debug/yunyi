# Agent NetPilot 工程设计文档（AI 实现版）

**版本**：0.1.0  
**状态**：设计稿，可直接交给 AI 编码代理实现  
**项目名**：`agent-netpilot`  
**定位**：为本地 AI Coding Harness（Claude Code、Codex CLI 等）提供弱网韧性层。  
**工具形态**：CLI 包装器 + 本地守护进程 + MCP Server + 离线执行器。  
**许可证建议**：MIT 或 Apache-2.0。

---

## 0. 给 AI 编码代理的指令

你正在实现 `agent-netpilot`。请严格按本文档实现，优先完成 MVP，不要过度设计。实现顺序：

1. 初始化 Python 项目、配置、数据模型。
2. 实现网络探测器与网络状态机。
3. 实现 SQLite 持久化。
4. 实现 CLI 包装器与守护进程。
5. 实现 MCP Server。
6. 实现预测性规划器提示词与计划存储。
7. 实现离线执行器。
8. 实现恢复、回滚与测试。
9. 编写文档与示例。

每个模块必须有单元测试。所有网络与执行行为必须可观测、可恢复、可回滚。

---

## 1. 背景与问题

本地 AI Coding Harness 与网页端不同：网页端任务在云端执行，浏览器只是观察窗口；本地 Harness 的“大脑”在云端，但“手脚”在用户电脑上。它需要不断向云端模型发送请求，获取下一步指令，再在本地执行命令、读写文件。

在高铁、隧道、弱 Wi-Fi 等场景下，网络抖动会导致：

- Harness 卡在等待 API 返回，不报错、不推进。
- 内部重试耗尽后任务中止。
- 用户看着进程挂起，无法判断是在思考还是已断网。
- 重新恢复后上下文丢失，需要重来。

`agent-netpilot` 的目标是：**感知网络、择时调用云端、提前规划、离线执行、恢复后同步**。

---

## 2. 目标与非目标

### 2.1 目标

- 实时检测网络质量，维护网络状态机。
- 在稳定窗口内集中进行云端 API 调用与规划。
- 网络变差或离线时，自动切换到离线执行预生成任务。
- 所有任务、步骤、检查点持久化到本地 SQLite。
- 支持断点续跑、恢复后评估、必要回滚。
- 以 CLI 包装器 + MCP Server 形式集成 Claude Code / Codex CLI。
- 不修改 Harness 源码。

### 2.2 非目标

- 不训练模型。
- 不替代 Claude Code / Codex CLI。
- 不保证所有任务都能离线完成。
- 不实现多用户云端协作。
- 不默认执行高风险命令。

---

## 3. 核心术语

| 术语 | 含义 |
|---|---|
| Harness | 本地 AI 编码代理，如 Claude Code、Codex CLI |
| 云端脑 | 远端大模型 API |
| NetPilot Daemon | 本地守护进程，负责网络监控与状态发布 |
| 稳定窗口 | 预测未来一段时间网络可用的时间段 |
| 规划器 | 调用云端模型，生成可离线执行的任务计划 |
| 离线执行器 | Python Loop，按计划在本地执行任务 |
| 检查点 | 任务执行过程中的可恢复状态快照 |
| 回滚 | 根据事务日志撤销或修正离线操作 |

---

## 4. 总体架构

```text
+---------------------+        +----------------------+
| Claude Code / Codex | <----> | NetPilot MCP Server  |
+---------------------+        +----------------------+
          ^                              ^
          |                              |
          v                              v
+---------------------+        +----------------------+
| Harness Wrapper CLI | <----> | NetPilot Daemon      |
+---------------------+        | - 网络探测           |
          |                    | - 状态机             |
          v                    | - 稳定窗口预测       |
+---------------------+        +----------------------+
| Offline Executor    | <----> | Persistence SQLite   |
| - 任务队列          |        | - 会话/计划/任务     |
| - 命令执行          |        | - 检查点/回滚日志    |
| - 检查点            |        +----------------------+
+---------------------+
```

### 4.1 数据流

1. 用户通过 `netpilot run -- claude ...` 启动 Harness。
2. Daemon 持续探测网络，维护状态。
3. 网络稳定时，MCP 通知 Harness 或 Planner 调用云端模型生成计划。
4. 计划被拆解为任务与步骤，写入 SQLite。
5. 网络变差，Daemon 发出 `OFFLINE` 事件。
6. Wrapper 暂停 Harness 的云端调用，启动离线执行器。
7. 离线执行器执行预生成任务，记录检查点。
8. 网络恢复，Daemon 发出 `RECOVERING` 事件。
9. Planner 读取离线结果，调用云端模型评估，决定继续、修正或回滚。

---

## 5. 网络状态机

### 5.1 状态定义

```python
class NetworkState(str, Enum):
    ONLINE_STABLE = "online_stable"
    ONLINE_UNSTABLE = "online_unstable"
    OFFLINE = "offline"
    RECOVERING = "recovering"
```

### 5.2 探测指标

- 探测目标：`https://api.anthropic.com`、`https://api.openai.com`、`1.1.1.1`。
- 探测间隔：默认 3000 ms。
- 超时：默认 2000 ms。
- 连续成功阈值：3 次进入 `ONLINE_STABLE`。
- 连续失败阈值：3 次进入 `OFFLINE`。
- 延迟与丢包率用于计算网络质量分。

### 5.3 状态转换

| 当前状态 | 条件 | 新状态 |
|---|---|---|
| ONLINE_STABLE | 连续失败 >= 阈值 | ONLINE_UNSTABLE |
| ONLINE_UNSTABLE | 连续失败 >= 阈值 | OFFLINE |
| ONLINE_UNSTABLE | 连续成功 >= 阈值 | ONLINE_STABLE |
| OFFLINE | 连续成功 >= 1 | RECOVERING |
| RECOVERING | 连续成功 >= 阈值 | ONLINE_STABLE |
| RECOVERING | 再次失败 | OFFLINE |

### 5.4 稳定窗口预测

Daemon 维护最近 60 秒探测结果，输出：

```json
{
  "state": "online_stable",
  "quality": 0.92,
  "stable_window_seconds": 45,
  "confidence": 0.8
}
```

稳定窗口用于规划器决定“这次能规划多少任务”。

---

## 6. 运行模式

| 模式 | 触发 | 行为 |
|---|---|---|
| NORMAL | ONLINE_STABLE | 正常调用云端，实时执行 |
| WEAK_NET | ONLINE_UNSTABLE | 减少 API 调用，优先保存检查点 |
| OFFLINE_EXEC | OFFLINE | 启动离线执行器，执行预生成任务 |
| RECOVERY | RECOVERING | 暂停离线执行，同步结果，云端评估 |

---

## 7. 组件详细设计

### 7.1 NetPilot Daemon

职责：

- 周期性探测网络。
- 维护状态机。
- 发布事件到本地事件总线。
- 提供 MCP 工具查询接口。
- 管理离线执行器生命周期。

关键接口：

```python
class NetworkMonitor:
    async def start(self) -> None: ...
    def state(self) -> NetworkState: ...
    async def wait_for_stable(self, min_seconds: int, timeout: float) -> bool: ...
    def snapshot(self) -> NetworkSnapshot: ...
```

### 7.2 Harness Wrapper CLI

职责：

- 包装 `claude`、`codex` 等命令。
- 注入环境变量，例如 `NETPILOT_SESSION_ID`。
- 监听 Daemon 事件。
- 网络进入 `OFFLINE` 时，暂停 Harness 的云端调用。
- 网络恢复后，恢复 Harness 或提示用户。

命令示例：

```bash
netpilot run --session my-task -- claude
netpilot run --session my-task -- codex
```

### 7.3 Planner

职责：

- 在稳定窗口内调用云端模型。
- 使用专用提示词，要求模型输出结构化计划。
- 将计划写入 SQLite。
- 计划必须包含可离线执行的命令、依赖、回滚策略。

### 7.4 Offline Executor

职责：

- 从 SQLite 读取待执行任务。
- 按依赖顺序执行。
- 每个步骤前后写检查点。
- 支持超时、失败重试、回滚。
- 不执行 denylist 命令。
- 危险命令需要用户确认或跳过。

伪代码：

```python
async def run(session_id: str):
    while True:
        task = queue.pop_next(session_id)
        if not task:
            break
        checkpoint = save_checkpoint(task, step=0, state={})
        try:
            for i, cmd in enumerate(task.commands):
                result = await run_command(cmd, timeout=task.timeout)
                save_step_result(task.id, i, result)
                save_checkpoint(task, step=i + 1, state=result.state)
        except Exception as e:
            mark_failed(task, e)
            if task.rollback_on_failure:
                rollback(checkpoint.id)
```

### 7.5 Persistence

使用 SQLite，默认路径：`~/.netpilot/netpilot.db`。

核心表：

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  harness TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE network_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  state TEXT,
  quality REAL,
  created_at TEXT
);

CREATE TABLE plans (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  network_budget_seconds INTEGER,
  raw_json TEXT,
  created_at TEXT
);

CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  plan_id TEXT,
  description TEXT,
  depends_on TEXT,
  commands TEXT,
  timeout INTEGER,
  rollback TEXT,
  risk TEXT,
  status TEXT
);

CREATE TABLE checkpoints (
  id TEXT PRIMARY KEY,
  task_id TEXT,
  step INTEGER,
  state_json TEXT,
  created_at TEXT
);

CREATE TABLE file_changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  path TEXT,
  change_type TEXT,
  diff TEXT,
  created_at TEXT
);

CREATE TABLE rollback_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  checkpoint_id TEXT,
  command TEXT,
  result TEXT,
  created_at TEXT
);
```

### 7.6 MCP Server

暴露工具给支持 MCP 的 Harness：

| 工具 | 说明 |
|---|---|
| `netpilot_get_state` | 返回当前网络状态 |
| `netpilot_wait_for_stable` | 等待稳定窗口 |
| `netpilot_save_plan` | 保存规划器输出 |
| `netpilot_enqueue_tasks` | 入队离线任务 |
| `netpilot_get_pending_tasks` | 获取待执行任务 |
| `netpilot_checkpoint` | 写入检查点 |
| `netpilot_rollback` | 回滚到检查点 |
| `netpilot_report_result` | 上报执行结果 |

MCP 工具输入输出使用 JSON Schema 定义，内部用 Pydantic 校验。

### 7.7 Rollback

回滚策略：

- 优先使用 Git：`git diff`、`git stash`、`git checkout -- <file>`。
- 非 Git 文件：保存变更前副本到 `~/.netpilot/snapshots/`。
- 每个任务可声明 `rollback` 命令。
- 回滚操作本身写入 `rollback_log`。

---

## 8. 接口设计

### 8.1 CLI

```bash
netpilot run --session <id> -- <harness-cmd>
netpilot status --session <id>
netpilot plan --session <id> --task "<description>"
netpilot offline-exec --session <id>
netpilot recover --session <id>
netpilot mcp
netpilot daemon
```

### 8.2 配置文件

`~/.netpilot/config.toml`：

```toml
[network]
probe_targets = ["https://api.anthropic.com", "https://api.openai.com", "1.1.1.1"]
probe_interval_ms = 3000
timeout_ms = 2000
stable_success_threshold = 3
offline_failure_threshold = 3
stable_window_min_seconds = 30

[offline]
executor = "python"
max_parallel = 1
checkpoint_interval = 1
command_allowlist = ["ls", "cat", "grep", "pytest", "npm test", "git diff", "git status"]
command_denylist = ["rm -rf /", "curl | sh", "wget | sh"]

[planner]
model = "claude-sonnet"
max_plan_seconds = 300
risk_preference = "low"
```

### 8.3 环境变量

- `NETPILOT_SESSION_ID`
- `NETPILOT_DB_PATH`
- `NETPILOT_LOG_LEVEL`
- `NETPILOT_OFFLINE_MODE`

---

## 9. 预测性规划提示词

### 9.1 系统提示词

```text
你是 Agent NetPilot 的规划器。当前网络状态：{state}。
预计稳定窗口：{stable_window_seconds} 秒。
网络预算：约 {network_budget_seconds} 秒。
风险偏好：{risk_preference}。

请将用户任务拆解为可离线执行的子任务。要求：
1. 每个子任务包含明确的本地命令。
2. 命令必须尽量幂等、可检查、可回滚。
3. 禁止高风险命令。
4. 如果信息不足，优先生成“探索性只读命令”。
5. 输出严格 JSON，不要额外解释。
```

### 9.2 输出 JSON Schema

```json
{
  "plan_id": "string",
  "network_budget_seconds": 300,
  "tasks": [
    {
      "id": "t1",
      "description": "运行测试并收集失败信息",
      "depends_on": [],
      "commands": ["pytest -q"],
      "timeout": 120,
      "expected_output": "测试失败列表",
      "rollback": "git checkout -- .",
      "risk": "low"
    }
  ]
}
```

---

## 10. 恢复与回滚流程

1. Daemon 检测到 `RECOVERING`。
2. Wrapper 暂停离线执行器。
3. Planner 读取离线执行结果与检查点。
4. 调用云端模型评估：
   - 哪些任务成功？
   - 哪些变更需要保留？
   - 哪些需要回滚？
   - 下一步计划是什么？
5. 执行回滚或修正。
6. 更新 SQLite，进入 `ONLINE_STABLE` 后继续正常模式。

---

## 11. 安全与权限

- 默认禁止 `rm -rf /`、`curl | sh` 等危险命令。
- 命令白名单可配置。
- 离线执行器默认串行执行。
- 所有文件变更写入快照。
- MCP 工具调用需要本地会话 ID。
- 敏感环境变量不写入日志。

---

## 12. 可观测性

日志格式：JSONL，路径 `~/.netpilot/logs/`。

关键指标：

- 网络状态切换次数。
- 稳定窗口平均长度。
- 离线任务成功/失败数。
- 检查点写入次数。
- 回滚次数。
- API 调用节省时间估算。

---

## 13. 测试计划

### 13.1 单元测试

- 网络状态机转换。
- 稳定窗口预测。
- SQLite 读写。
- 命令白名单/黑名单。
- 检查点与回滚。

### 13.2 集成测试

- 模拟网络抖动：使用 `toxiproxy` 或自定义 HTTP 代理。
- 启动 fake harness，验证暂停/恢复。
- MCP 工具调用端到端。

### 13.3 端到端测试

- 模拟高铁场景：稳定 30 秒 -> 断网 60 秒 -> 恢复。
- 验证任务不丢失、检查点可恢复、回滚可执行。

---

## 14. MVP 路线

| 阶段 | 内容 | 验收 |
|---|---|---|
| Phase 1 | Daemon + 网络状态机 + CLI 包装器 | 断网时能检测并记录 |
| Phase 2 | SQLite + 检查点 + MCP Server | 可保存/恢复会话 |
| Phase 3 | 规划器提示词 + 任务队列 | 稳定窗口生成计划 |
| Phase 4 | 离线执行器 + 回滚 | 断网后执行预生成任务 |
| Phase 5 | 多 Harness 适配 + 文档 | Claude Code / Codex 可用 |

---

## 15. 目录结构

```text
agent-netpilot/
  pyproject.toml
  README.md
  docs/
    design.md
    prompts/
  src/netpilot/
    __init__.py
    cli.py
    daemon.py
    network.py
    state_machine.py
    persistence.py
    planner.py
    offline_executor.py
    mcp_server.py
    wrapper.py
    rollback.py
    models.py
    config.py
  tests/
    test_network.py
    test_state_machine.py
    test_persistence.py
    test_offline_executor.py
    test_mcp.py
  examples/
    config.toml
    plan.json
```

---

## 16. 技术选型

- Python 3.11+
- `asyncio`、`httpx`、`psutil`
- `typer` 或 `click` 做 CLI
- `pydantic` 做模型校验
- `sqlite3` 或 `aiosqlite`
- `mcp` Python SDK
- `gitpython` 或直接调用 `git`
- `pytest`、`pytest-asyncio`

---

## 17. 验收标准

- 模拟断网 30 秒，Harness 不崩溃，任务暂停并保存检查点。
- 网络恢复后 5 秒内自动继续或提示恢复。
- 稳定窗口内 API 调用成功率 > 95%。
- 离线执行器可断点续跑。
- 所有命令执行有日志、有检查点、可回滚。
- MCP 工具可被 Claude Code 调用。
- 文档包含配置、示例、故障排查。

---

## 18. 参考项目与调研方向

- `cc-resilient`：Claude Code 网络韧性包装器。
- `aimem`：本地 SQLite 会话持久化。
- `picclaw`：离线优先 Agent 状态机。
- `@moolam/edge-agent`：离线认知循环与 CRDT 同步。
- `The Haymaker Method`：云编排器 + 本地模型双节点拓扑。
- `DarkMatter`：基于 MCP 的 Agent 网状通信。

实现前建议调研这些项目的接口与许可证，但不要直接复制代码。

---

## 19. 开放问题

1. 如何在不修改 Harness 源码的情况下，可靠暂停其云端调用？
2. 稳定窗口预测是否需要机器学习，还是规则足够？
3. 离线执行器是否应该支持并行？并行时如何保证依赖与回滚？
4. 多 Harness 适配层如何抽象？
5. 是否需要与 Git 深度集成，自动创建临时分支？

---

## 20. 最终交付物

AI 编码代理应交付：

- 可运行的 `agent-netpilot` Python 包。
- CLI：`netpilot run/status/plan/offline-exec/recover/mcp/daemon`。
- MCP Server。
- SQLite 持久化。
- 预测性规划提示词模板。
- 离线执行器。
- 测试套件。
- README 与示例配置。
- 开源许可证。

---

以上文档可直接作为 AI 编码代理的项目规格。建议 AI 先实现 Phase 1 和 Phase 2，验证网络状态机与持久化，再逐步实现规划器与离线执行器。