# Brief: yunyi-integration

## 问题与当前状态
用户需要以 yunyi run 包装现有 Harness，并通过 MCP/CLI 保存计划、查看网络、执行与恢复。已验证 MCP SDK stdio，尚未验证真实 Harness 联机调用。

## 期望结果与方案
组合基础和执行能力，先跑 fake harness 最小闭环，再适配 Claude Code 与 Codex。MCP 提供协作入口；本地守护进程独立维护状态；规划由受限的既有 Harness 非交互适配器产生结构化计划。

## 范围
- 包含：七类 CLI、daemon 生命周期、八项 MCP 工具、Harness 生命周期、规划及恢复编排、集成验收与交付。
- 排除：修改 Harness 源码、拦截任意 TLS 请求、保证暂停在途云请求或计费、自动改写用户全局 Harness 配置。

## Boundary Candidates
- CLI、Daemon、HarnessAdapter、MCPServer、Planner、IntegrationTests。

## 上下游与约束
- 上游：yunyi-foundation、yunyi-execution。
- 下游：用户现有 Claude/Codex 及本地 MCP 客户端。
- 既有规格扩展：无。真实联机认证/计费/自动恢复的验收独立于 fake harness。
- 规划失败不入队；模型建议与本地执行授权分离；不新增密钥存储。
