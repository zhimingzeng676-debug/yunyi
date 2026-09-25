# 调研与设计决策：集成

## 摘要
MCP依赖及真实Harness最小结构化联机调用已实测；完整网络恢复与TTY控制仍待产品验收，不能标成完整产品GO。

## SDK试验
实际stdio客户端连接独立server进程，initialize/list_tools/call_tool和领域错误通过。第一次返回裸dict，structuredContent=None导致测试失败；改用Pydantic返回模型后原测试通过。协议stdout与stderr日志分离。

## 客户端接口调查
- Claude Code本机2.1.282，help确认print、json output/schema、tools及mcp配置参数；这里只是接口发现。
- Codex本机0.155.0-alpha.9.2，help确认exec、read-only、ephemeral、output-schema、output-last-message、ignore-user-config。
- 官方非交互文档说明结构化输出及只读执行选项；实际参数以当前本机help为准。[Codex官方文档](https://learn.chatgpt.com/docs/non-interactive-mode)
- 后续串行各发起一次固定ready测试，Claude5.28秒、Codex18.98秒，均退出0且返回ready=true。没有读取密钥或修改全局MCP配置；本轮没有真实客户端断网恢复或长期成功率证据。
- Claude npm启动器实际指向bin/claude.exe，并非旧版cli.js；第一次旧入口发现失败未发起云请求，修正后使用实际原生exe。
- Claude真实输出字段是structured_output（同时有字符串result）；原始duration/usage/terminal_reason均保留。Codex从output-last-message文件获得JSON，JSONL显示没有命令或工具调用。
- 固定测试prompt不含项目文件；客户端仍可能自动加载其自身系统提示与用户规则，因此正式Planner应使用项目外独立临时目录，避免继承项目AGENTS/skills。

## 架构方案
1. 本地MCP+账本协作：依赖少、兼容性可单独验收，采用。
2. TLS透明代理：涉及客户端配置、认证和协议差异，本轮不采用。
3. 仅暂停进程：不能控制远端在途请求，也不证明工作区安全交接，不作为充分方案。

## 决策
先导入计划与fake harness闭环，实际客户端adapter必须先独立spike再实现。MCP通知不保证触发Harness自动调用模型，因此默认通过CLI显式规划或现有会话合作保存计划。

五秒指标从RECOVERING事件计时，保证提示和停止新派发；物理链路恢复到探测有采样延迟。完整自动云续跑不得用该指标偷换。

## 未关闭门禁
Claude/Codex受限联机依赖已通过；MCP真实宿主配置、TTY/控制台、断网恢复和100请求统计保留为产品发布验收。用户只批准了多规格路线，生成的具体需求/设计/任务审批字段仍为false。

## 来源与证据
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x)
- [MCP取消语义](https://modelcontextprotocol.io/specification/2025-06-18/basic/utilities/cancellation)
- docs/evidence/dependency-spikes-before-fix.log、dependency-spikes.log。
- docs/evidence/claude-live-spike.json、codex-live-spike.json、claude-launcher-discovery-failure.json。
- 已读取本机claude --help与codex exec --help；日志中不含认证配置。
