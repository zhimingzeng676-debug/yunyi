# 云驿（yunyi） 规格审阅入口

当前阶段：命名迁移已完成；Discovery与依赖spike已执行，三份完整requirements/design/tasks仍等待用户逐份确认。命名迁移的确认不等于规格批准。尚未进入kiro-impl，没有产品代码，也没有开启并行实现。

新旧名称及历史证据映射见[命名迁移说明](naming-migration.md)。本文链接指向迁移后的规格，原始实验结果保持原样；新机械追踪结果为[evidence/yunyi-sdd-mechanical-check.json](evidence/yunyi-sdd-mechanical-check.json)。

## 规格包

| 规格 | 内容 | 需求 | 设计 | 任务 |
|---|---|---|---|---|
| yunyi-foundation | 配置、网络状态、模型、账本、日志 | [requirements](../.kiro/specs/yunyi-foundation/requirements.md) | [design](../.kiro/specs/yunyi-foundation/design.md) | [tasks](../.kiro/specs/yunyi-foundation/tasks.md) |
| yunyi-execution | 策略、进程、执行、快照、回滚、核对 | [requirements](../.kiro/specs/yunyi-execution/requirements.md) | [design](../.kiro/specs/yunyi-execution/design.md) | [tasks](../.kiro/specs/yunyi-execution/tasks.md) |
| yunyi-integration | CLI、daemon、MCP、Harness、规划、验收 | [requirements](../.kiro/specs/yunyi-integration/requirements.md) | [design](../.kiro/specs/yunyi-integration/design.md) | [tasks](../.kiro/specs/yunyi-integration/tasks.md) |

共72条可验收需求、40个执行单元（其中2项真实CLI前置spike已完成，38项产品/工具链实施任务待执行）。方向已于本对话获确认；各spec.json的具体requirements/design/tasks批准字段保持false，避免把方向确认冒充规格批准。

## 建议确认的行为边界

1. **暂停与接管**：只管理本地进程，不能撤回在途云请求。普通暂停不自动许可离线写入；合作交接或用户结束Harness后才能安全接管同一工作区。真实Claude/Codex默认保守提示，不宣传无缝自动接管已实现。
2. **执行与回滚**：默认只执行精确本地批准的动作。受管文件快照可还原任务开始前的真实脏内容；普通外部命令不获得通用沙箱或任意副作用回滚保证。未知结果暂停核对，不盲重跑。
3. **恢复指标**：首次成功探测触发RECOVERING后五秒内提示并停止新领取；不把它等同于物理链路恢复后五秒内完成云端续跑。
4. **并发**：先单条完整TDD流水线和最小闭环；通过后才评估互不写同一文件的任务并发。离线执行器运行时并发仍固定1。

以上是spike证明需要的准确边界，不是删去后续真实适配或恢复验收。若需要“无人值守自动切换真实Harness并修改同一工作区”，还需额外可靠合作协议或隔离工作区方案，不能用psutil暂停冒充。

## 实施顺序

1. 通过本文具体规格审阅，写入真实批准状态。
2. 建立开发分支，执行foundation并通过上游契约验收。
3. 执行execution并通过故障注入、回滚互斥与重启核对。
4. 执行integration 1至3组，跑通真实SDK/fake harness/受控探针/文件和账本闭环；证明已完成步骤不重跑。
5. 接入已spike的真实规划适配器、云恢复评估和中文交付；运行实际默认30秒稳定/60秒断网轨迹。
6. 分别验收真实Claude/Codex MCP/TTY/恢复；真实成功率统计需单独明确运行的样本，不从探针推算。

每项行为：独立测试作者 → 可解释真实RED → 隔离代码作者 → 未改测试GREEN → 规格/对抗/质量三项审查 → 选择性提交。spec/task状态不得抢先标完成。

## 原始稿追踪

| 原稿章节 | 规格落点与处理 |
|---|---|
| 1–4 背景、目标、架构 | 三份brief与steering；保留CLI+daemon+MCP+executor |
| 5–6 网络与模式 | foundation需求2–3；明确失败计数与恢复计时 |
| 7.1–7.3 daemon/wrapper/planner | integration需求1、2、4 |
| 7.4 执行器 | execution需求1–3，严格审批与未知状态 |
| 7.5 持久化 | foundation需求4–5，补充复合归属、步骤和回滚父子账本 |
| 7.6 MCP | integration需求3，保留八工具并限制结果伪造 |
| 7.7及10 恢复回滚 | execution需求4–5，integration4.5；弃用破坏性整仓回滚 |
| 8 CLI/配置/环境 | foundation1，integration1；旧字符串计划显式迁移 |
| 9 规划提示词 | integration4，打包版本化模板 |
| 11–12 安全/可观测 | foundation6、execution1/4、integration3 |
| 13–17 测试/路线/技术/验收 | 各规格测试策略、integration5，Windows/Python依赖实测 |
| 18 参考项目 | 仅作调研方向；未采用其代码或引入未核验依赖 |
| 19 开放问题 | 采用规则窗口、运行串行、明确适配能力、字节快照 |
| 20 交付 | integration5.3与README/示例/MIT/LICENSE任务 |

## 验证入口

[Spike报告](spike-report.md)包含39项通过的本地测试、真实RED/GREEN、两次CLI最小联机结果及工具链负对照。[机械追踪检查](evidence/sdd-mechanical-check.json)验证需求映射与任务编号；独立设计与任务图结论见[evidence/sdd-reviews.md](evidence/sdd-reviews.md)。这些证明准备工作，不证明产品完成。
