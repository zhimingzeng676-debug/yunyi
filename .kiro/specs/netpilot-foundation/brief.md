# Brief: netpilot-foundation

## 问题与当前状态
弱网下的本地开发者缺少可信的网络状态和可恢复任务账本；当前只有设计稿与隔离 spike，无产品代码。

## 期望结果与方案
提供经过验证的配置、网络观测、四态转换、结构化计划模型和事务账本，供 CLI/MCP 与执行器共同使用。使用规则估计窗口，不用机器学习；标准库 SQLite 本地存储。

## 范围
- 包含：会话、计划、步骤、事件、检查点、审计模型，网络探测与等待，结构化日志。
- 排除：启动 Harness、执行命令、生成云计划和实施回滚。

## Boundary Candidates
- Configuration/Models、NetworkMonitor、Repository、AuditLog。

## 上下游与约束
- 上游：Python 3.11+ 与已验依赖。
- 下游：netpilot-execution 和 netpilot-integration。
- 既有规格扩展：无；本规格拥有共享数据契约，禁止下游另建平行模型。
- 所有技术变更以实际 spike 为证据；SQLite 3.51.1 禁用多连接 WAL。
