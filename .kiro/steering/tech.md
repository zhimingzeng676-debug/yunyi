# 技术与验证约束

- Python 3.11+；本机执行器 D:/anaconda3/envs/pack311/python.exe。初始 spike 依赖在 .tools/python，.spikes/bootstrap 处理 pywin32 .pth；产品安装采用正常 conda site-packages，不能依赖该临时 bootstrap。
- 已验版本：mcp 1.30.0、pydantic 2.13.5、httpx 0.28.1、psutil 7.2.2、typer 0.27.2、pytest 9.1.1。精确解析版本在 docs/evidence/python-dependencies.lock。
- SQLite 标准库实际为 3.51.1；默认 DELETE journal + synchronous=FULL，foreign_keys=ON，busy_timeout=5000。当前版本不得开启多连接 WAL；以后启用需运行时版本检查及重新 spike。
- MCP 仅 stdio。Pydantic 返回模型生成 outputSchema 和 structuredContent；裸 dict 未生成结构化返回的试验失败已记录。
- shell=False、argv 列表、显式可执行程序解析；禁止 shell 字符串和命令前缀白名单。受管命令不被宣称为操作系统安全沙箱。
- 不持有数据库事务等待子进程；领取与落库分开，崩溃窗口用 needs_reconciliation 表示。
- 产品所有行为单元先写测试，真实收集并运行 RED，断言失败原因必须对应新增行为。收集失败、无测试、超时、缺少运行器不得算 RED。
- 原始 Agentic TDD verify-red 会把不存在的运行器误判为通过；必须附加 pytest 原始退出码=1、JUnit tests>0、errors=0、failures>0、预期失败 case 校验。原始 check-state 不验证审查结论，需要额外审查完整性门禁。
- 每单元测试文件 SHA256 在 RED 后冻结；改测试需重走 RED，不能覆盖旧证据。代码作者不接收测试作者推理。
- 三种独立审查：规格一致性、对抗性、代码质量。审查拒绝后修复必须重新审查；最终 kiro-validate-impl + 新鲜完整测试。
- 长于原始验证器 30 秒上限的真实轨迹单列端到端运行，保留日志与结果，不冒充其 GREEN 子集。
