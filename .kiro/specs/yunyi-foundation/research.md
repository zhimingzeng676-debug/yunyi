# 调研与设计决策：基础

## 摘要
全新项目，采用完整 discovery。已核验 Python 3.11.14、SDK依赖、真实 SQLite 多进程事务、HTTP 探测分类；证据见 docs/evidence。

## 调研记录

### 运行时与 SDK
- 本机 y 是 Python 3.10.20，pack311 是3.11.14；采用后者，符合用户允许使用其他已列 conda 环境的约束。
- 实际安装 mcp 1.30.0 与 Pydantic 2.13.5，不混用SDK v2接口；版本锁保存在 python-dependencies.lock。
- MCP Windows 依赖 pywin32；--target安装不自动处理.pth，第一次collection失败。spike加入site.addsitedir后导入通过；正式包采用正常安装，独立验收正常安装路径。

### SQLite
- sqlite3实际版本3.51.1。
- 官方说明WAL-reset bug影响截至3.51.2的WAL多连接并发写/检查点；本版本选择DELETE/FULL，不强行开启WAL。[官方说明](https://www.sqlite.org/wal.html#walresetbug)
- 真实两进程竞争只有一方领取；事务内更新后os._exit，重开保留原状态且integrity_check=ok。
- 外部文件已写、数据库尚未commit时崩溃，文件仍在但账本仍running。这是未知结果核对的依据，不是恰好执行一次证明。

### 测试工具链
- cc-sdd 3.1.0通过官方Codex Skills安装器装入项目，68个文件；未覆盖已有文件。[官方仓库](https://github.com/gotalab/cc-sdd)
- agentic-tdd 5.2.1原始脚本在本机Claude目录，使用项目锁定tsx执行。
- 隔离单元真实RED为18失败/12通过，GREEN30通过，hash未变；三项独立审查通过，check-state返回consistent=true。
- 负对照发现不存在的测试命令也被原始verify-red接受，因此附加原始退出码、JUnit收集结果与预期失败断言门禁。原始failureCount计算函数数，不是参数化失败case数。

## 方案与决策
规则状态机优于未有训练数据的预测模型；SQLite短事务优于新引入消息中间件；采用现成SDK而非手写MCP协议。仅共享Plan/Step契约，不引入通用插件框架。

## 风险与待验
正式安装和wheel冒烟在foundation 1.1完成；新工具链门禁必须包含负对照；稳定窗口不是概率保证；多连接WAL不在本轮实现范围。

## 来源
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x)
- [SQLite事务原子性](https://www.sqlite.org/atomiccommit.html)
- [SQLite同步设置](https://www.sqlite.org/pragma.html#pragma_synchronous)
- 本地证据：docs/evidence/dependency-spikes.log、tdd-red-tests.log、verify-green.json、verifier-negative-control.json。
