# 目录与责任

- .kiro/specs/netpilot-foundation：基础配置、模型、状态和持久化的唯一规格来源。
- .kiro/specs/netpilot-execution：动作执行、检查点、快照、回滚与恢复。
- .kiro/specs/netpilot-integration：用户命令、进程编排、MCP 和规划。
- src/netpilot：产品代码，目前未创建。
- tests/unit、tests/integration、tests/e2e：依需求派生的产品测试，目前未创建。
- .spikes：抛弃式依赖验证；不属于产品测试或发布内容。
- docs/evidence：原始测试日志、JUnit、验证器返回及审查结果。
- .tools：本项目临时工具依赖，Git 忽略。
- docs/source-design.md：用户原始设计稿，保留原意。
- docs/sdd-review.md：规格总入口、原稿差异、验收状态。

开发分支与独立工作树在进入正式实现前建立；阶段提交只包含明确文件，不执行全目录暂存，不做破坏性重置。
