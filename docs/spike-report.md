# 依赖与工作流 Spike 报告

日期：2026-09-26。范围仅为技术依赖和开发工作流；产品尚未实现。

## 已执行实验

| 实验 | 实际结果 | 对设计的影响 |
|---|---|---|
| Python/依赖 | pack311 3.11.14；SDK及测试依赖已安装并锁定 | 不使用系统Python或y的3.10运行本项目 |
| MCP stdio | 真实initialize、工具列表、schema、调用、错误返回通过 | 采用mcp 1.30.0与Pydantic返回模型 |
| HTTP探测 | HTTP401响应能证明连通，不能证明API可用 | 分离connectivity和认证/API成功率 |
| Windows暂停 | 暂停父进程不停止子进程；逐个暂停/恢复可观测 | best_effort不自动授予写入交接 |
| Windows Job | 挂起创建→加入Job→恢复；关闭Job后父子均退出 | 使用Job控制离线命令树生命周期 |
| SQLite竞争 | 两进程只有一方领取；crash后未提交更新回滚 | 短事务与令牌版本比较 |
| 外部副作用 | 文件写完后crash，数据库仍running | needs_reconciliation，不盲重放 |
| argv与快照原语 | shell=False保留特殊字符；快照保留脏字节，hash发现外部改动 | 精确参数审批、条件回滚 |
| Claude真实调用 | 原生CLI 2.1.282；5.28秒；退出0；structured_output.ready=true | 使用原生exe及已验受限参数 |
| Codex真实调用 | CLI 0.155.0-alpha.9.2；18.98秒；退出0；JSON ready=true；无命令/工具事件 | 使用read-only、ephemeral、schema与结果文件 |

最终本地测试：**39 passed in 12.33s**，包括9个依赖实验和30个TDD单元用例。真实CLI调用单独验证，不能与pytest用例混算。两次CLI invocation可能各自包含客户端内部请求，不能声称只产生两次底层API请求。

## Agentic TDD 证据

1. Test Writer使用独立上下文创建测试与恒False占位。
2. 实际pytest RED：18 failed、12 passed，退出1，无collection error。
3. 原始verify-red执行成功，记录测试SHA256。
4. Code Writer使用新的隔离上下文，只读磁盘测试，只修改实现。
5. 原始verify-green：30 passed，测试hash未变，无skip。
6. 三位独立审查者依次给出COMPLIANT、PASS、Approved。
7. 原始check-state consistent=true，generate-report成功。原始报告把4个测试函数计作Tests written/失败数，真实参数化计数应以JUnit和pytest日志为准。
8. 故意修改测试副本但保持30项测试通过时，GREEN验证器退出1，确认hash门禁有效。

## 已发现并处置的工具链问题

- --target依赖目录未处理pywin32.pth，首次MCP collection失败。spike使用site.addsitedir；正式项目必须通过正常安装与wheel验收。
- MCP返回裸dict未提供structuredContent，原测试失败。改为Pydantic返回模型后同一测试通过。
- 原始verify-red对不存在的运行器也返回passed。补充门禁必须检查真实退出码、JUnit收集/错误/失败数与预期失败case，不得只信它的status。
- 原始check-state不验证三类审查是否齐全；项目流程另行校验。
- 审查提示输出PASS，但原始报告期望passed。适配层保留原始结论并规范化状态；否则报告误报对抗审查失败。attempt计数由实际派发次数补录，未修改测试证明。
- Claude安装结构已变为原生bin/claude.exe，旧cli.js入口失败。修正实际入口后才发送最小请求。
- SQLite 3.51.1处于官方WAL-reset受影响范围，采用DELETE/FULL，不开启多连接WAL。

## 证据入口

- [完整本地测试](evidence/final-spike-tests.log)
- [RED原始失败](evidence/tdd-red-tests.log)
- [GREEN与hash](evidence/verify-green.json)
- [独立审查](evidence/tdd-independent-reviews.json)
- [假RED负对照](evidence/verifier-negative-control.json)
- [测试篡改负对照](evidence/tampered-green-negative-control.json)
- [汇总核验](evidence/preflight-verification.json)
- [Claude真实请求](evidence/claude-live-spike.json)
- [Codex真实请求](evidence/codex-live-spike.json)

## 未包含的验收

本报告不证明产品七类CLI、八工具、最小闭环、完整回滚、真实Harness MCP连接/TTY/断网恢复或稳定窗口API成功率已完成。它们在规格任务中保留，必须实现后实际验证。受限测试prompt没有附带项目文件，但客户端可能自动加载自己的系统/用户规则，正式规划应使用项目外临时目录。
