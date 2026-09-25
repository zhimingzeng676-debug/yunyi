# 云驿（yunyi）

为本地 Claude Code / Codex CLI 等 Coding Harness 提供弱网韧性层，计划形态为 CLI 包装器、本地守护进程、MCP Server 和离线执行器。

**当前只有规格与依赖试验，没有可安装的产品代码。** 三份规格的审批仍为false；命名迁移没有启动产品实现，也未建立实施开发分支。

## 入口

- [规格审阅总入口](docs/sdd-review.md)
- [路线图](.kiro/steering/roadmap.md)
- [依赖spike报告](docs/spike-report.md)
- [命名、环境变量与旧安装迁移说明](docs/naming-migration.md)

## 统一命名

计划中的包与CLI均为`yunyi`，模块目录为`src/yunyi/`，默认数据目录为`~/.yunyi/`，数据库为`yunyi.db`。
配置环境变量为`YUNYI_SESSION_ID`、`YUNYI_DB_PATH`、`YUNYI_LOG_LEVEL`、`YUNYI_OFFLINE_MODE`。兼容读取规则仅在迁移说明中介绍，尚未实现。

文档可使用副名：候风（网络探测与状态机）、风信（稳定窗口）、栖风（离线执行器）、驻云（检查点与账本）、回风（恢复与核对）、驿使（MCP八工具）。代码标识只使用英文名。

## MCP配置模板

[Claude Code模板](examples/claude-mcp.json)与[Codex模板](examples/codex-mcp.toml)使用统一server名`yunyi`，仅供未来产品安装后采用，**目前不能启动产品服务**。示例会话`example`需要先按届时实现的CLI创建；Python路径按本机已验pack311填写，其他机器需修改。

不会自动改写用户全局客户端配置。旧server条目迁移及数据目录的一次性复制步骤见[迁移说明](docs/naming-migration.md)。本次检查未发现`~/.netpilot/`、`~/.yunyi/`或仓库spike遗留数据库，没有搬动任何用户数据。

## 验证与下一步

本轮只验证名称引用、需求/任务顺序、审批状态和已有依赖实验；不新增产品行为，也不制造产品RED/GREEN记录。后续逐份获得规格批准后，才建立开发分支并执行`yunyi-foundation`，遵守真实RED、独立测试/实现/审查及最小闭环前串行的纪律。
