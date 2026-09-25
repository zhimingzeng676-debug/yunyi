# Brief: netpilot-execution

## 问题与当前状态
断网时预生成任务不能丢失；命令可能超时、产生副作用或在写账本前崩溃。已有依赖试验证明数据库事务不能回滚外部副作用。

## 期望结果与方案
在已授权且独占的工作区串行执行受管动作，保存前后检查点、输出和文件快照。结果未知时暂停核对，受管文件回滚保留任务开始前的脏改动。

## 范围
- 包含：动作权限、依赖调度、进程生命周期、快照、补偿、核对报告。
- 排除：任意 shell 程序的安全沙箱和无条件回滚、云端评估、网络状态判定。

## Boundary Candidates
- CommandPolicy、OfflineExecutor、SnapshotStore、RollbackService、RecoveryService、ProcessJob。

## 上下游与约束
- 上游：netpilot-foundation 的 Repository、Models、AuditLog。
- 下游：netpilot-integration 的 daemon/CLI/MCP 调用。
- 既有规格扩展：无。与 Harness 共享目录时，未能确保执行权交接就不自动写入。
- 默认并发为一；危险动作由用户本地授权，模型不能自行批准。
