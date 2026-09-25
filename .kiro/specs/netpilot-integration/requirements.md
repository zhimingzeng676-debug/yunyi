# 需求：用户入口与 Harness 集成

状态：完整审阅稿，真实客户端与云端验收独立于模拟测试。

## 项目描述
将网络观测、离线任务和恢复账本组合成可安装使用的 CLI/MCP 工具，不修改 Claude Code/Codex 源码。

## 1. CLI 与生命周期
用户故事：作为开发者，我希望从统一命令启动、查询、规划和恢复。

- 1.1 The NetPilot shall 提供 run、status、plan、offline-exec、recover、mcp、daemon 七类命令以及中文快速开始、示例配置、示例计划、故障排查和许可证。
- 1.2 When 包装 Harness，the NetPilot shall 保留原参数边界和终端输入输出，注入当前会话标识，并传播正常退出码；启动失败应给出明确错误。
- 1.3 When 启动 daemon，the NetPilot shall 保证同一账本只有一个有效监控所有者，允许 status/MCP 读取最新状态；退出或崩溃后可安全重启。
- 1.4 If daemon 不可用或状态陈旧，the NetPilot shall 明确显示降级，禁止自动启动离线写入，不用缓存状态冒充正常服务。

## 2. Harness 弱网交接
用户故事：作为开发者，我希望断网时客户端状态可解释，并在安全时执行本地工作。

- 2.1 When 进入 OFFLINE，the NetPilot shall 记录事件并请求受管 Harness 暂停或合作让出执行权，返回逐进程结果；已发出的云请求保留 in_flight/unknown 标记。
- 2.2 If Harness 无法可靠交出工作区控制权，the NetPilot shall 提示用户，并阻止同一工作区自动写入；不得把进程暂停成功等同于所有远端请求取消。
- 2.3 When 首次成功探测触发 RECOVERING，the NetPilot shall 在五秒内向用户发出恢复提示并停止派发新的离线步骤；该计时不包含此前物理网络恢复到首次探测的时间。
- 2.4 When 当前离线步骤收尾且恢复决策完成，the NetPilot shall 仅恢复由本系统暂停且身份仍匹配的进程，或给出明确的手动恢复说明。
- 2.5 The NetPilot shall 分别记录 Claude Code、Codex 和 generic adapter 的实际能力及验证版本，不以 fake harness 通过替代真实客户端通过。

## 3. MCP 协作入口
用户故事：作为支持 MCP 的 Harness，我希望通过结构化工具与本地账本协作。

- 3.1 The NetPilot shall 暴露 netpilot_get_state、netpilot_wait_for_stable、netpilot_save_plan、netpilot_enqueue_tasks、netpilot_get_pending_tasks、netpilot_checkpoint、netpilot_rollback、netpilot_report_result 八项工具，并提供输入输出 schema。
- 3.2 When 调用任何工具，the NetPilot shall 验证当前传输绑定的会话与请求会话一致，拒绝跨会话访问；会话标识本身不得被当成远程认证手段。
- 3.3 When 保存或入队计划，the NetPilot shall 校验结构和审批政策，返回 accepted、rejected 或 pending_approval；保存操作不能自动执行命令。
- 3.4 When MCP 上报结果、写检查点或请求回滚，the NetPilot shall 校验有效步骤凭证、状态版本和所属工作区，拒绝伪造完成和过期操作。
- 3.5 If 工具执行失败或等待超时，the NetPilot shall 返回结构化错误且不污染协议输出，并允许后续合法请求继续。

## 4. 预测规划
用户故事：作为开发者，我希望在稳定时准备离线任务，并避免执行损坏的模型输出。

- 4.1 When 发起规划，the NetPilot shall 仅在非陈旧稳定状态及足够预算下调用选定规划适配器，将网络估计、风险政策和用户任务提供给它。
- 4.2 When 获得模型计划，the NetPilot shall 校验严格结构、依赖、动作能力及预算后保存，并保持执行审批独立。
- 4.3 If 网络恶化、调用超时、认证失败、模型返回无效计划或没有可用适配器，the NetPilot shall 保留原有计划并报告原因，不保存半份新计划或无限重试。
- 4.4 The NetPilot shall 提供版本化规划与恢复提示词模板，并支持导入已生成计划及导出提示词，使无云凭据的本地闭环可验证。
- 4.5 When 网络恢复后请求云评估，the NetPilot shall 只提交用户已授权的结果摘要，验证返回决策，并通过本地恢复规则执行；调用失败保持待评估而不擅自回滚。

## 5. 可验证交付
用户故事：作为项目验收者，我希望模拟闭环和真实兼容性都有独立证据。

- 5.1 The NetPilot shall 通过稳定三十秒、断网六十秒、再次恢复的可控端到端轨迹，证明预置任务不丢失、检查点存在、已完成步骤不重复执行及受管回滚可核对。
- 5.2 The NetPilot shall 在最小闭环中连接真实 MCP SDK 客户端、fake harness、可控探针及真实文件系统/账本，并在进程重启后继续验证结果。
- 5.3 Where 执行真实客户端验收，the NetPilot shall 分别给出 Claude/Codex 的连接、规划、断网和恢复结果及版本；缺少凭据或无法安全完成时保持未验收状态。
- 5.4 When 报告稳定窗口内 API 成功率，the NetPilot shall 记录实际请求分母、窗口判定及失败类别；原稿大于百分之九十五目标仅按约定真实测试样本评估，不以网络探针替代。
- 5.5 The NetPilot shall 在每个行为单元保留真实 RED、未改测试的 GREEN、独立审查及新鲜完整测试证据，最小闭环和工具链未通过前不得扩大实现并发。

## 边界与相邻期待
状态与数据规则由 foundation 提供，动作执行和回滚由 execution 提供。本规格只编排调用，不新增旁路数据库写入或绕过权限。默认安全边界变化需用户审阅后再实施。
